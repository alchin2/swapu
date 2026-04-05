import logging

from core.exceptions import NotFoundError, ValidationError
from service.chat_service import ChatService
from service.deal_service import DealService
from service.negotiation_service import NegotiationService
from service.base import SupabaseService

logger = logging.getLogger(__name__)

ACTIVE_STATUSES = ("pending", "negotiating", "accepted")

CONDITION_RANK = {"like_new": 4, "good": 3, "fair": 2, "poor": 1}


class MatchingService(SupabaseService):

    def create_best_agent_deal(
        self,
        user_id: str,
        category: str | None = None,
        condition: str | None = None,
    ) -> dict:
        """Agent-driven flow: auto-discover user's collection, find the best
        mutual match, create a deal, and run negotiation.

        The agent pulls ALL of the user's items (their collection) and their
        wanted categories (user_categories), then finds other users who have
        stuff the user wants AND want what the user can offer — all within the
        user's max_cash_amt / max_cash_pct limits.
        """
        user_id = self.require_identifier(user_id, "user_id")
        logger.info("Agent auto-deal for user=%s", user_id[:8])

        # 1. Get ALL items owned by this user (their collection)
        all_items = (
            self.client.table("items")
            .select("id")
            .eq("owner_id", user_id)
            .execute()
        ).data
        if not all_items:
            raise ValidationError("User has no items in their collection to trade.")

        # 2. Exclude items already locked in active deals
        active_deals = (
            self.client.table("deals")
            .select("user1_item_id, user2_item_id")
            .in_("status", list(ACTIVE_STATUSES))
            .execute()
        ).data
        busy_ids = set()
        for d in active_deals:
            busy_ids.add(d["user1_item_id"])
            busy_ids.add(d["user2_item_id"])

        available_ids = [i["id"] for i in all_items if i["id"] not in busy_ids]
        if not available_ids:
            raise ValidationError("All of the user's items are already in active deals.")

        logger.info("User has %d available items out of %d total", len(available_ids), len(all_items))

        # 3. Find the best match using the full collection
        matches = self.find_matches(
            user_id=user_id,
            item_ids=available_ids,
            category=category,
            condition=condition,
            limit=1,
        )
        if not matches:
            raise NotFoundError("No eligible trade match was found for agent negotiation.")

        best_match = matches[0]
        deal_service = DealService()
        chat_service = ChatService()
        negotiation_service = NegotiationService()

        deal = deal_service.create_deal({
            "user1_id": user_id,
            "user2_id": best_match["other_user_id"],
            "user1_item_id": best_match["my_offer_item_id"],
            "user2_item_id": best_match["other_item_id"],
            "cash_difference": best_match["price_diff"],
            "payer_id": best_match["who_pays"],
            "status": "pending",
        })
        chatroom = chat_service.create_chatroom(deal["id"])

        return {
            "selected_match": best_match,
            "deal": deal,
            "chatroom": chatroom,
            "next_actions": self._build_next_actions(deal["status"]),
        }

    @staticmethod
    def run_negotiation_background(deal_id: str) -> None:
        """Run AI negotiation in a background task (called after response is sent)."""
        try:
            NegotiationService().start_negotiation(deal_id)
            logger.info("Background negotiation completed for deal %s", deal_id)
        except Exception:
            logger.exception("Background negotiation failed for deal %s", deal_id)

    def find_matches(
        self,
        user_id: str,
        item_ids: list[str],
        category: str | None = None,
        name: str | None = None,
        condition: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """Find best trade matches for a user's items.

        Args:
            user_id: The searching user — pulls max_cash_amt/max_cash_pct.
            item_ids: Items the user is willing to offer.
            category: Filter results to this category.
            name: Partial text search on item name (case-insensitive).
            condition: Minimum condition filter (good/fair/poor/like_new).
            limit: Max results to return.
        """
        user_id = self.require_identifier(user_id, "user_id")
        if not item_ids:
            raise ValidationError("item_ids must contain at least one item.")
        logger.info("Finding matches for user=%s offering %d items", user_id[:8], len(item_ids))

        # 1. Fetch the user's cash constraints
        user = (
            self.client.table("users")
            .select("id, max_cash_amt, max_cash_pct")
            .eq("id", user_id)
            .single()
            .execute()
        ).data
        if not user:
            raise NotFoundError(f"User '{user_id}' not found.")
        max_cash_amt = float(user.get("max_cash_amt") or 0)
        max_cash_pct = float(user.get("max_cash_pct") or 0) / 100.0

        # 2. Fetch the user's offered items
        my_items = (
            self.client.table("items")
            .select("id, owner_id, name, category, price")
            .in_("id", item_ids)
            .eq("owner_id", user_id)
            .execute()
        ).data
        if not my_items:
            raise ValidationError("No valid offered items were found for this user.")
        logger.info("Offering items: %s", [(i["name"], i["category"], i["price"]) for i in my_items])

        my_categories = {i["category"] for i in my_items}
        # 3. Fetch what I want (user_categories)
        my_cats_rows = (
            self.client.table("user_categories")
            .select("category")
            .eq("user_id", user_id)
            .execute()
        ).data
        my_wanted = set()
        for row in my_cats_rows:
            for cat in row["category"].split(","):
                cat = cat.strip()
                if cat:
                    my_wanted.add(cat)
        logger.info("I want categories: %s", my_wanted)

        # Apply category filter if provided
        if category:
            my_wanted = {c for c in my_wanted if c.lower() == category.lower()}
        if not my_wanted:
            return []

        # 4. Find other users who want at least one of MY item categories
        all_cats = (
            self.client.table("user_categories")
            .select("user_id, category")
            .neq("user_id", user_id)
            .execute()
        ).data
        users_who_want_mine = set()
        for row in all_cats:
            cats = {c.strip() for c in row["category"].split(",") if c.strip()}
            if cats & my_categories:  # any overlap
                users_who_want_mine.add(row["user_id"])
        logger.info("Users who want my categories (%s): %d", my_categories, len(users_who_want_mine))

        if not users_who_want_mine:
            return []

        # 5. Find items from those users matching my wanted categories
        query = (
            self.client.table("items")
            .select("id, owner_id, name, category, condition, price")
            .in_("owner_id", list(users_who_want_mine))
            .in_("category", list(my_wanted))
        )
        if name:
            query = query.ilike("name", f"%{name}%")
        candidate_items = query.execute().data
        logger.info("Candidate items (before filters): %d", len(candidate_items))

        if not candidate_items:
            return []

        # 6. Filter by minimum condition
        if condition:
            min_rank = CONDITION_RANK.get(condition, 0)
            candidate_items = [
                ci for ci in candidate_items
                if CONDITION_RANK.get(ci.get("condition", ""), 0) >= min_rank
            ]
            logger.info("After condition filter (>=%s): %d", condition, len(candidate_items))

        # 7. Filter out items already in active deals
        active_deals = (
            self.client.table("deals")
            .select("user1_item_id, user2_item_id")
            .in_("status", list(ACTIVE_STATUSES))
            .execute()
        ).data
        busy_item_ids = set()
        for d in active_deals:
            busy_item_ids.add(d["user1_item_id"])
            busy_item_ids.add(d["user2_item_id"])

        candidates = [ci for ci in candidate_items if ci["id"] not in busy_item_ids]
        logger.info("After active-deal filter: %d", len(candidates))

        # 8. Filter by cash affordability — find best pairing per candidate
        affordable = []
        for c in candidates:
            other_price = float(c["price"])
            # Find the best item to offer against this candidate (smallest gap)
            best_pair = None
            best_diff = float("inf")
            for mi in my_items:
                diff = other_price - float(mi["price"])
                if diff > 0:
                    # I'd need to pay cash
                    max_payable = min(max_cash_amt, float(mi["price"]) * max_cash_pct)
                    if diff > max_payable:
                        continue
                abs_diff = abs(diff)
                if abs_diff < best_diff:
                    best_diff = abs_diff
                    best_pair = mi
            if best_pair:
                affordable.append((c, best_pair, best_diff))
        logger.info("After affordability filter: %d", len(affordable))

        if not affordable:
            return []

        # 9. Fetch user names
        owner_ids = list({c["owner_id"] for c, _, _ in affordable})
        users = (
            self.client.table("users")
            .select("id, name")
            .in_("id", owner_ids)
            .execute()
        ).data
        name_map = {u["id"]: u["name"] for u in users}

        # 10. Build results, rank by smallest price diff
        affordable.sort(key=lambda x: x[2])
        results = []
        for c, best_offer, price_diff in affordable[:limit]:
            other_price = float(c["price"])
            offer_price = float(best_offer["price"])
            who_pays = user_id if offer_price < other_price else c["owner_id"]
            if offer_price == other_price:
                who_pays = None

            results.append({
                "other_user_id": c["owner_id"],
                "other_user_name": name_map.get(c["owner_id"], "Unknown"),
                "other_item_id": c["id"],
                "other_item_name": c["name"],
                "other_item_category": c["category"],
                "other_item_condition": c.get("condition"),
                "other_item_price": other_price,
                "my_offer_item_id": best_offer["id"],
                "my_offer_item_name": best_offer["name"],
                "my_offer_item_price": offer_price,
                "price_diff": round(price_diff, 2),
                "who_pays": who_pays,
            })

        logger.info("Returning %d matches", len(results))
        return results

    @staticmethod
    def _build_next_actions(deal_status: str) -> list[str]:
        if deal_status == "negotiating":
            return ["accept", "decline", "counter"]
        if deal_status == "accepted":
            return ["view_deal"]
        if deal_status == "declined":
            return ["search_again"]
        return ["start_negotiation"]
