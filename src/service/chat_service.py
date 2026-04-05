from core.exceptions import AuthorizationError, ConflictError, NotFoundError, ValidationError
from service.base import SupabaseService


class ChatService(SupabaseService):
    def _get_chatroom(self, chatroom_id: str) -> dict:
        chatroom_id = self.require_identifier(chatroom_id, "chatroom_id")
        result = (
            self.client.table("chatrooms")
            .select("id, deal_id, deals(user1_id, user2_id, status)")
            .eq("id", chatroom_id)
            .limit(1)
            .execute()
        )
        chatroom = self.first_or_none(result)
        if chatroom is None:
            raise NotFoundError(f"Chatroom '{chatroom_id}' not found.")
        return chatroom

    def create_chatroom(self, deal_id: str) -> dict:
        """Create a chatroom linked to a deal. Only one chatroom per deal."""
        deal_id = self.require_identifier(deal_id, "deal_id")
        deal = (
            self.client.table("deals")
            .select("id, user1_id, user2_id, status")
            .eq("id", deal_id)
            .limit(1)
            .execute()
        )
        if not deal.data:
            raise NotFoundError(f"Deal '{deal_id}' not found.")

        existing = (
            self.client.table("chatrooms")
            .select("id")
            .eq("deal_id", deal_id)
            .limit(1)
            .execute()
        )
        if existing.data:
            raise ConflictError(f"Chatroom already exists for deal '{deal_id}'.")

        result = self.client.table("chatrooms").insert({"deal_id": deal_id}).execute()
        return result.data[0]

    def delete_chatroom(self, chatroom_id: str) -> dict:
        """Delete a chatroom and its messages."""
        chatroom = self._get_chatroom(chatroom_id)

        self.client.table("messages").delete().eq("chatroom_id", chatroom["id"]).execute()
        self.client.table("chatrooms").delete().eq("id", chatroom_id).execute()

        return {"message": f"Chatroom '{chatroom_id}' deleted successfully."}

    def get_chatroom(self, chatroom_id: str) -> dict:
        """Get chatroom details including the deal's participants."""
        chatroom = self._get_chatroom(chatroom_id)
        deal = chatroom.get("deals") or {}
        return {"id": chatroom["id"], "deal_id": chatroom["deal_id"], "deals": deal}

    def get_chatrooms_by_user(self, user_id: str) -> list:
        """Get all chatrooms a user is part of (via deals)."""
        user_id = self.require_identifier(user_id, "user_id")
        deals = (
            self.client.table("deals")
            .select("id")
            .or_(f"user1_id.eq.{user_id},user2_id.eq.{user_id}")
            .execute()
        )
        if not deals.data:
            return []

        deal_ids = [d["id"] for d in deals.data]

        chatrooms = (
            self.client.table("chatrooms")
            .select("id, deal_id, deals(id, user1_id, user2_id, status)")
            .in_("deal_id", deal_ids)
            .execute()
        )
        return chatrooms.data

    def get_messages(self, chatroom_id: str, limit: int = 50) -> list:
        """Get messages in a chatroom, ordered by creation time."""
        chatroom = self._get_chatroom(chatroom_id)

        result = (
            self.client.table("messages")
            .select("id, chatroom_id, sender_id, content, created_at")
            .eq("chatroom_id", chatroom["id"])
            .order("created_at", desc=False)
            .limit(limit)
            .execute()
        )
        return result.data

    def send_message(self, chatroom_id: str, sender_id: str, content: str) -> dict:
        """Send a message in a chatroom (REST fallback before WS is ready)."""
        sender_id = self.require_identifier(sender_id, "sender_id")
        normalized_content = content.strip()
        if not normalized_content:
            raise ValidationError("Message content cannot be empty.")
        chatroom = self._get_chatroom(chatroom_id)

        deal = chatroom.get("deals") or {}
        if sender_id not in [deal.get("user1_id"), deal.get("user2_id")]:
            raise AuthorizationError("User is not a participant in this chatroom.")

        result = (
            self.client.table("messages")
            .insert(
                {
                    "chatroom_id": chatroom["id"],
                    "sender_id": sender_id,
                    "content": normalized_content,
                }
            )
            .execute()
        )
        return result.data[0]
