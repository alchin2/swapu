from database.supabase_client import get_supabase_client


class ChatService:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = get_supabase_client()
        return self._client

    def create_chatroom(self, deal_id: str) -> dict:
        """Create a chatroom linked to a deal. Only one chatroom per deal."""
        # Verify the deal exists
        deal = (
            self.client.table("deals")
            .select("id, user1_id, user2_id, status")
            .eq("id", deal_id)
            .single()
            .execute()
        )
        if not deal.data:
            raise ValueError(f"Deal {deal_id} not found")

        # Check if a chatroom already exists for this deal
        existing = (
            self.client.table("chatrooms")
            .select("id")
            .eq("deal_id", deal_id)
            .execute()
        )
        if existing.data:
            raise ValueError(f"Chatroom already exists for deal {deal_id}")

        # Create the chatroom
        result = (
            self.client.table("chatrooms")
            .insert({"deal_id": deal_id})
            .execute()
        )
        return result.data[0]

    def delete_chatroom(self, chatroom_id: str) -> dict:
        """Delete a chatroom and its messages."""
        # Verify chatroom exists
        chatroom = (
            self.client.table("chatrooms")
            .select("id, deal_id")
            .eq("id", chatroom_id)
            .single()
            .execute()
        )
        if not chatroom.data:
            raise ValueError(f"Chatroom {chatroom_id} not found")

        # Delete messages in the chatroom first
        self.client.table("messages").delete().eq(
            "chatroom_id", chatroom_id
        ).execute()

        # Delete the chatroom
        self.client.table("chatrooms").delete().eq("id", chatroom_id).execute()

        return {"message": f"Chatroom {chatroom_id} deleted successfully"}

    def get_chatroom(self, chatroom_id: str) -> dict:
        """Get chatroom details including the deal's participants."""
        result = (
            self.client.table("chatrooms")
            .select("id, deal_id, deals(id, user1_id, user2_id, status)")
            .eq("id", chatroom_id)
            .single()
            .execute()
        )
        if not result.data:
            raise ValueError(f"Chatroom {chatroom_id} not found")
        return result.data

    def get_chatrooms_by_user(self, user_id: str) -> list:
        """Get all chatrooms a user is part of (via deals)."""
        # Find all deals where the user is either user1 or user2
        deals = (
            self.client.table("deals")
            .select("id")
            .or_(f"user1_id.eq.{user_id},user2_id.eq.{user_id}")
            .execute()
        )
        if not deals.data:
            return []

        deal_ids = [d["id"] for d in deals.data]

        # Get chatrooms for those deals
        chatrooms = (
            self.client.table("chatrooms")
            .select("id, deal_id, deals(id, user1_id, user2_id, status)")
            .in_("deal_id", deal_ids)
            .execute()
        )
        return chatrooms.data

    def get_messages(self, chatroom_id: str, limit: int = 50) -> list:
        """Get messages in a chatroom, ordered by creation time."""
        # Verify chatroom exists
        chatroom = (
            self.client.table("chatrooms")
            .select("id")
            .eq("id", chatroom_id)
            .single()
            .execute()
        )
        if not chatroom.data:
            raise ValueError(f"Chatroom {chatroom_id} not found")

        result = (
            self.client.table("messages")
            .select("id, chatroom_id, sender_id, content, created_at")
            .eq("chatroom_id", chatroom_id)
            .order("created_at", desc=False)
            .limit(limit)
            .execute()
        )
        return result.data

    def send_message(self, chatroom_id: str, sender_id: str, content: str) -> dict:
        """Send a message in a chatroom (REST fallback before WS is ready)."""
        # Verify chatroom exists
        chatroom = (
            self.client.table("chatrooms")
            .select("id, deal_id, deals(user1_id, user2_id)")
            .eq("id", chatroom_id)
            .single()
            .execute()
        )
        if not chatroom.data:
            raise ValueError(f"Chatroom {chatroom_id} not found")

        # Verify sender is a participant in the deal
        deal = chatroom.data.get("deals", {})
        if sender_id not in [deal.get("user1_id"), deal.get("user2_id")]:
            raise PermissionError("User is not a participant in this chatroom")

        result = (
            self.client.table("messages")
            .insert(
                {
                    "chatroom_id": chatroom_id,
                    "sender_id": sender_id,
                    "content": content,
                }
            )
            .execute()
        )
        return result.data[0]
