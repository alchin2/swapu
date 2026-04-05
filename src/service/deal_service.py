from core.exceptions import NotFoundError, ValidationError
from service.base import SupabaseService


class DealService(SupabaseService):
    def _get_existing_deal(self, deal_id: str) -> dict:
        deal_id = self.require_identifier(deal_id, "deal_id")
        result = (
            self.client.table("deals")
            .select("*")
            .eq("id", deal_id)
            .limit(1)
            .execute()
        )
        return self.first_or_raise(result, f"Deal '{deal_id}' not found.")

    def create_deal(self, deal_data: dict) -> dict:
        """Create a new deal."""
        if deal_data["user1_id"] == deal_data["user2_id"]:
            raise ValidationError("A deal requires two different users.")
        if deal_data["user1_item_id"] == deal_data["user2_item_id"]:
            raise ValidationError("A deal requires two different items.")
        result = self.client.table("deals").insert(deal_data).execute()
        if not result.data:
            raise ValidationError("Failed to create deal.")
        return result.data[0]

    def get_deal(self, deal_id: str) -> dict:
        """Fetch a specific deal by ID."""
        return self._get_existing_deal(deal_id)

    def get_user_deals(self, user_id: str) -> list:
        """Fetch all deals involving a specific user."""
        user_id = self.require_identifier(user_id, "user_id")
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
            raise ValidationError("No valid fields provided for update.")

        self._get_existing_deal(deal_id)

        result = (
            self.client.table("deals")
            .update(deal_data)
            .eq("id", deal_id)
            .execute()
        )

        if not result.data:
            raise NotFoundError(f"Deal '{deal_id}' not found.")
        return result.data[0]

    def delete_deal(self, deal_id: str) -> dict:
        """Delete a deal."""
        self._get_existing_deal(deal_id)
        self.client.table("deals").delete().eq("id", deal_id).execute()
        return {"message": f"Deal '{deal_id}' deleted successfully."}
