from database.supabase_client import get_supabase_client
from agents.negotiation_runner import run_negotiation, UserContext


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
        # 1. Fetch the deal
        deal = (
            self.client.table("deals")
            .select("id, user1_id, user2_id, user1_item_id, user2_item_id, cash_difference, payer_id, status")
            .eq("id", deal_id)
            .single()
            .execute()
        )
        if not deal.data:
            raise ValueError(f"Deal {deal_id} not found")

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
            user1_item_price=float(item1["price"]),
            user2_item_price=float(item2["price"]),
        )

        # 6. Log negotiation steps to neg_logs
        for log in outcome["logs"]:
            self.client.table("neg_logs").insert({
                "deal_id": deal_id,
                "agent": log["agent"],
                "content": log["content"],
                "step": log["step"],
            }).execute()

        # 7. Update the deal with the result
        result = outcome["result"]
        if result["status"] == "accepted":
            self.client.table("deals").update({
                "cash_difference": result["final_cash_difference"],
                "payer_id": result["final_payer_id"],
                "status": "accepted",
            }).eq("id", deal_id).execute()
        else:
            self.client.table("deals").update({
                "status": "declined",
            }).eq("id", deal_id).execute()

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
