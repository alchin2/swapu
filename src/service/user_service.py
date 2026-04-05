import uuid
from typing import Optional

from core.exceptions import ConflictError, NotFoundError, ValidationError
from service.base import SupabaseService

USERS_TABLE = "users"

class UserService(SupabaseService):
    def _validate_cash_preferences(
        self,
        max_cash_amt: Optional[float],
        max_cash_pct: Optional[float],
    ) -> None:
        if max_cash_amt is not None and max_cash_amt < 0:
            raise ValidationError("max_cash_amt must be greater than or equal to zero.")
        if max_cash_pct is not None and not 0 <= max_cash_pct <= 100:
            raise ValidationError("max_cash_pct must be between 0 and 100.")

    def _get_user_or_raise(self, user_id: str) -> dict:
        user_id = self.require_identifier(user_id, "user_id")
        response = (
            self.client.table(USERS_TABLE)
            .select("*")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        return self.first_or_raise(response, f"User '{user_id}' not found.")

    def create_user(
        self,
        email: str,
        name: str,
        max_cash_amt: Optional[float] = None,
        max_cash_pct: Optional[float] = None,
    ) -> dict:
        """Create a new user."""
        normalized_email = self.require_identifier(email, "email").lower()
        normalized_name = self.require_identifier(name, "name")
        self._validate_cash_preferences(max_cash_amt, max_cash_pct)

        existing = (
            self.client.table(USERS_TABLE)
            .select("id")
            .eq("email", normalized_email)
            .limit(1)
            .execute()
        )
        if existing.data:
            raise ConflictError(f"A user with email '{normalized_email}' already exists.")

        new_user = {
            "id": str(uuid.uuid4()),
            "email": normalized_email,
            "name": normalized_name,
            "max_cash_amt": max_cash_amt,
            "max_cash_pct": max_cash_pct,
        }
        response = self.client.table(USERS_TABLE).insert(new_user).execute()
        return response.data[0]

    def get_user_by_id(self, user_id: str) -> dict:
        """Fetch a single user by UUID."""
        return self._get_user_or_raise(user_id)

    def get_user_by_email(self, email: str) -> dict:
        """Fetch a single user by email."""
        normalized_email = self.require_identifier(email, "email").lower()
        response = (
            self.client.table(USERS_TABLE)
            .select("*")
            .eq("email", normalized_email)
            .limit(1)
            .execute()
        )
        return self.first_or_raise(response, f"No user found with email '{normalized_email}'.")

    def update_user(
        self,
        user_id: str,
        name: Optional[str] = None,
        max_cash_amt: Optional[float] = None,
        max_cash_pct: Optional[float] = None,
    ) -> dict:
        """Update mutable fields on an existing user."""
        user_id = self.require_identifier(user_id, "user_id")
        self._get_user_or_raise(user_id)
        self._validate_cash_preferences(max_cash_amt, max_cash_pct)

        updates: dict = {}
        if name is not None:
            updates["name"] = self.require_identifier(name, "name")
        if max_cash_amt is not None:
            updates["max_cash_amt"] = max_cash_amt
        if max_cash_pct is not None:
            updates["max_cash_pct"] = max_cash_pct

        if not updates:
            return self._get_user_or_raise(user_id)

        response = self.client.table(USERS_TABLE).update(updates).eq("id", user_id).execute()
        return response.data[0]

    def delete_user(self, user_id: str) -> dict:
        """Delete a user and associated records across dependent tables."""
        user_id = self.require_identifier(user_id, "user_id")
        self._get_user_or_raise(user_id)

        self.client.table("messages").delete().eq("sender_id", user_id).execute()

        deals = (
            self.client.table("deals")
            .select("id")
            .or_(f"user1_id.eq.{user_id},user2_id.eq.{user_id}")
            .execute()
        )
        deal_ids = [deal["id"] for deal in deals.data or []]

        for deal_id in deal_ids:
            chatrooms = (
                self.client.table("chatrooms")
                .select("id")
                .eq("deal_id", deal_id)
                .execute()
            )
            for chatroom in chatrooms.data or []:
                self.client.table("messages").delete().eq("chatroom_id", chatroom["id"]).execute()
            self.client.table("chatrooms").delete().eq("deal_id", deal_id).execute()

        if deal_ids:
            self.client.table("deals").delete().in_("id", deal_ids).execute()

        self.client.table("items").delete().eq("owner_id", user_id).execute()
        self.client.table("user_categories").delete().eq("user_id", user_id).execute()
        self.client.table(USERS_TABLE).delete().eq("id", user_id).execute()

        return {"message": f"User '{user_id}' deleted successfully."}

    def list_users(self) -> list:
        """Return all users (used by frontend guest account selector)."""
        response = self.client.table(USERS_TABLE).select("*").execute()
        return response.data or []
