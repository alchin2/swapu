import logging

from database.supabase_client import get_supabase_client
from agents.negotiation_runner import run_negotiation, UserContext

logger = logging.getLogger(__name__)


class NegotiationService:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = get_supabase_client()
        return self._client

    def start_negotiation(self, deal_id: str) -> dict:
        """Kick off agent negotiation for a deal."""
        logger.info("Starting negotiation for deal_id=%s", deal_id)

        # 1. Fetch the deal
        deal = (
            self.client.table("deals")
            .select("id, user1_id, user2_id, user1_item_id, user2_item_id, cash_difference, payer_id, status")
            .eq("id", deal_id)
            .single()
            .execute()
        )
        if not deal.data:
            logger.error("Deal %s not found", deal_id)
            raise ValueError(f"Deal {deal_id} not found")

        logger.info("Deal fetched: status=%s, user1=%s, user2=%s",
                    deal.data['status'], deal.data['user1_id'][:8], deal.data['user2_id'][:8])

        if deal.data["status"] not in ("pending", "negotiating"):
            raise ValueError(f"Deal is already {deal.data['status']}, cannot negotiate")

        # 2. Fetch both users
        user1 = (
            self.client.table("users")
            .select("id, name, max_cash_amt, max_cash_pct")
            .eq("id", deal.data["user1_id"])
            .single()
            .execute()
        ).data
        user2 = (
            self.client.table("users")
            .select("id, name, max_cash_amt, max_cash_pct")
            .eq("id", deal.data["user2_id"])
            .single()
            .execute()
        ).data

        # 3. Fetch both items
        item1 = (
            self.client.table("items")
            .select("id, name, price")
            .eq("id", deal.data["user1_item_id"])
            .single()
            .execute()
        ).data
        item2 = (
            self.client.table("items")
            .select("id, name, price")
            .eq("id", deal.data["user2_item_id"])
            .single()
            .execute()
        ).data

        # 4. Build user contexts
        ctx1 = UserContext(
            user_id=user1["id"],
            item_price=float(item1["price"]),
            max_cash_amt=float(user1["max_cash_amt"]),
            max_cash_pct=float(user1["max_cash_pct"]),
        )
        ctx2 = UserContext(
            user_id=user2["id"],
            item_price=float(item2["price"]),
            max_cash_amt=float(user2["max_cash_amt"]),
            max_cash_pct=float(user2["max_cash_pct"]),
        )

        # 5. Run the negotiation
        outcome = run_negotiation(
            deal_id=deal_id,
            user1=ctx1,
            user2=ctx2,
        )

        # 6. Log negotiation steps to neg_logs
        logger.info("Writing %d log entries to neg_logs for deal %s", len(outcome["logs"]), deal_id)
        for log in outcome["logs"]:
            try:
                self.client.table("neg_logs").insert({
                    "deal_id": deal_id,
                    "agent": log["agent"],
                    "content": log["content"],
                    "step": log["step"],
                }).execute()
                logger.info("  Wrote step %d: %s", log["step"], log["agent"])
            except Exception as e:
                logger.error("  Failed to write step %d: %s", log["step"], e)

        # 7. Update the deal with the result
        result = outcome["result"]
        logger.info("Negotiation result: status=%s, cash=$%.2f, payer=%s",
                    result["status"], result["final_cash_difference"],
                    result["final_payer_id"][:8] if result["final_payer_id"] else "none")

        if result["status"] == "accepted":
            # Agents agreed — set to 'negotiating' so user can confirm/counter/decline
            self.client.table("deals").update({
                "cash_difference": result["final_cash_difference"],
                "payer_id": result["final_payer_id"],
                "status": "negotiating",
            }).eq("id", deal_id).execute()
            logger.info("Deal %s updated to negotiating (awaiting user confirmation)", deal_id)
        else:
            self.client.table("deals").update({
                "status": "declined",
            }).eq("id", deal_id).execute()
            logger.info("Deal %s updated to declined", deal_id)

        # 8. Also post a summary message to the chatroom if one exists
        chatroom = (
            self.client.table("chatrooms")
            .select("id")
            .eq("deal_id", deal_id)
            .execute()
        )
        if chatroom.data:
            summary = (
                f"Negotiation complete: {result['status']}. "
                f"Cash difference: ${result['final_cash_difference']:.2f}"
            )
            self.client.table("messages").insert({
                "chatroom_id": chatroom.data[0]["id"],
                "sender_id": ctx1.user_id,  # system message attributed to user1
                "content": f"[AGENT] {summary}",
            }).execute()

        return outcome

    def confirm_negotiation(self, deal_id: str) -> dict:
        """User confirms the negotiated deal."""
        deal = self._get_deal(deal_id)
        if deal["status"] != "negotiating":
            raise ValueError(f"Deal is '{deal['status']}', must be 'negotiating' to confirm")

        self.client.table("deals").update({
            "status": "accepted",
        }).eq("id", deal_id).execute()
        logger.info("Deal %s confirmed -> accepted", deal_id)
        return {"deal_id": deal_id, "status": "accepted"}

    def decline_negotiation(self, deal_id: str) -> dict:
        """User declines the negotiated deal."""
        deal = self._get_deal(deal_id)
        if deal["status"] != "negotiating":
            raise ValueError(f"Deal is '{deal['status']}', must be 'negotiating' to decline")

        self.client.table("deals").update({
            "status": "declined",
        }).eq("id", deal_id).execute()
        logger.info("Deal %s declined", deal_id)
        return {"deal_id": deal_id, "status": "declined"}

    def counter_negotiation(self, deal_id: str, cash_difference: float, payer_id: str) -> dict:
        """User counters with new terms and re-runs negotiation."""
        deal = self._get_deal(deal_id)
        if deal["status"] != "negotiating":
            raise ValueError(f"Deal is '{deal['status']}', must be 'negotiating' to counter")

        # Update deal with user's counter values, reset to pending
        self.client.table("deals").update({
            "cash_difference": cash_difference,
            "payer_id": payer_id,
            "status": "pending",
        }).eq("id", deal_id).execute()
        logger.info("Deal %s counter: cash=$%.2f payer=%s, re-negotiating",
                    deal_id, cash_difference, payer_id[:8])

        # Re-run negotiation (which will set status back to negotiating/declined)
        return self.start_negotiation(deal_id)

    def _get_deal(self, deal_id: str) -> dict:
        """Fetch a deal by ID."""
        deal = (
            self.client.table("deals")
            .select("id, user1_id, user2_id, user1_item_id, user2_item_id, cash_difference, payer_id, status")
            .eq("id", deal_id)
            .single()
            .execute()
        )
        if not deal.data:
            raise ValueError(f"Deal {deal_id} not found")
        return deal.data

    def get_negotiation_logs(self, deal_id: str) -> list:
        """Get all negotiation logs for a deal."""
        result = (
            self.client.table("neg_logs")
            .select("id, deal_id, agent, content, step, created_at")
            .eq("deal_id", deal_id)
            .order("step", desc=False)
            .execute()
        )
        return result.data
