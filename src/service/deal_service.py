from database.supabase_client import get_supabase_client

class DealService:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = get_supabase_client()
        return self._client

    def create_deal(self, deal_data: dict) -> dict:
        """Create a new deal."""
        result = (
            self.client.table("deals")
            .insert(deal_data)
            .execute()
        )
        if not result.data:
            raise ValueError("Failed to create deal")
        return result.data[0]

    def get_deal(self, deal_id: str) -> dict:
        """Fetch a specific deal by ID."""
        result = (
            self.client.table("deals")
            .select("*")
            .eq("id", deal_id)
            .execute()
        )
        if not result.data:
            raise ValueError(f"Deal {deal_id} not found")
        # single() is removed as supabase returns empty data if not found, 
        # so array access is safe when data exists, or single() could throw if >1
        return result.data[0]

    def get_user_deals(self, user_id: str) -> list:
        """Fetch all deals involving a specific user."""
        result = (
            self.client.table("deals")
            .select("*")
            .or_(f"user1_id.eq.{user_id},user2_id.eq.{user_id}")
            .execute()
        )
        if not result.data:
            return []
        return result.data

    def update_deal(self, deal_id: str, deal_data: dict) -> dict:
        """Update a deal."""
        if not deal_data:
            raise ValueError("No valid fields provided for update")

        result = (
            self.client.table("deals")
            .update(deal_data)
            .eq("id", deal_id)
            .execute()
        )
        
        if not result.data:
            raise ValueError(f"Deal {deal_id} not found or update failed")
        return result.data[0]

    def delete_deal(self, deal_id: str) -> dict:
        """Delete a deal."""
        result = (
            self.client.table("deals")
            .delete()
            .eq("id", deal_id)
            .execute()
        )
        if not result.data:
            raise ValueError(f"Deal {deal_id} not found")
        return {"message": f"Deal {deal_id} deleted successfully"}
