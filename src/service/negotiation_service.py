import logging

from core.exceptions import ExternalServiceError, NotFoundError, ValidationError
from agents.negotiation_runner import run_negotiation, UserContext
from service.base import SupabaseService

logger = logging.getLogger(__name__)


class NegotiationService(SupabaseService):

    def start_negotiation(self, deal_id: str) -> dict:
        """Kick off agent negotiation for a deal."""
        deal_id = self.require_identifier(deal_id, "deal_id")
        logger.info("Starting negotiation for deal_id=%s", deal_id)

        # 1. Fetch the deal
        deal = (
            self.client.table("deals")
            .select("id, user1_id, user2_id, user1_item_id, user2_item_id, cash_difference, payer_id, status")
            .eq("id", deal_id)
            .limit(1)
            .execute()
        )
        if not deal.data:
            logger.error("Deal %s not found", deal_id)
            raise NotFoundError(f"Deal '{deal_id}' not found.")

        deal_row = deal.data[0]

        logger.info("Deal fetched: status=%s, user1=%s, user2=%s",
                    deal_row['status'], deal_row['user1_id'][:8], deal_row['user2_id'][:8])

        if deal_row["status"] not in ("pending", "negotiating"):
            raise ValidationError(f"Deal is already '{deal_row['status']}' and cannot be negotiated.")

        # 2. Fetch both users
        user1 = (
            self.client.table("users")
            .select("id, name, max_cash_amt, max_cash_pct")
            .eq("id", deal_row["user1_id"])
            .single()
            .execute()
        ).data
        user2 = (
            self.client.table("users")
            .select("id, name, max_cash_amt, max_cash_pct")
            .eq("id", deal_row["user2_id"])
            .single()
            .execute()
        ).data

        # 3. Fetch both items
        item1 = (
            self.client.table("items")
            .select("id, name, price")
            .eq("id", deal_row["user1_item_id"])
            .single()
            .execute()
        ).data
        item2 = (
            self.client.table("items")
            .select("id, name, price")
            .eq("id", deal_row["user2_item_id"])
            .single()
            .execute()
        ).data

        if not user1 or not user2:
            raise NotFoundError("One or more users on the deal no longer exist.")
        if not item1 or not item2:
            raise NotFoundError("One or more items on the deal no longer exist.")

        # 4. Build user contexts
        ctx1 = UserContext(
            user_id=user1["id"],
            item_price=float(item1["price"]),
            max_cash_amt=float(user1.get("max_cash_amt") or 0),
            max_cash_pct=float(user1.get("max_cash_pct") or 0),
        )
        ctx2 = UserContext(
            user_id=user2["id"],
            item_price=float(item2["price"]),
            max_cash_amt=float(user2.get("max_cash_amt") or 0),
            max_cash_pct=float(user2.get("max_cash_pct") or 0),
        )

        # 5. Run the negotiation
        try:
            outcome = run_negotiation(deal_id=deal_id, user1=ctx1, user2=ctx2)
        except Exception as exc:
            logger.exception("Negotiation runner failed for deal %s", deal_id, exc_info=exc)
            raise ExternalServiceError("Negotiation provider failed to produce a result.") from exc

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
            raise ValidationError(f"Deal is '{deal['status']}', must be 'negotiating' to confirm.")

        self.client.table("deals").update({
            "status": "accepted",
        }).eq("id", deal_id).execute()
        logger.info("Deal %s confirmed -> accepted", deal_id)
        return {"deal_id": deal_id, "status": "accepted"}

    def decline_negotiation(self, deal_id: str) -> dict:
        """User declines the negotiated deal."""
        deal = self._get_deal(deal_id)
        if deal["status"] != "negotiating":
            raise ValidationError(f"Deal is '{deal['status']}', must be 'negotiating' to decline.")

        self.client.table("deals").update({
            "status": "declined",
        }).eq("id", deal_id).execute()
        logger.info("Deal %s declined", deal_id)
        return {"deal_id": deal_id, "status": "declined"}

    def counter_negotiation(self, deal_id: str, cash_difference: float, payer_id: str) -> dict:
        """User counters with new terms and re-runs negotiation."""
        if cash_difference < 0:
            raise ValidationError("cash_difference must be greater than or equal to zero.")
        deal = self._get_deal(deal_id)
        if deal["status"] != "negotiating":
            raise ValidationError(f"Deal is '{deal['status']}', must be 'negotiating' to counter.")

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
        deal_id = self.require_identifier(deal_id, "deal_id")
        deal = (
            self.client.table("deals")
            .select("id, user1_id, user2_id, user1_item_id, user2_item_id, cash_difference, payer_id, status")
            .eq("id", deal_id)
            .limit(1)
            .execute()
        )
        if not deal.data:
            raise NotFoundError(f"Deal '{deal_id}' not found.")
        return deal.data[0]

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
