import uuid
from typing import Optional

from core.exceptions import ConflictError, NotFoundError, ValidationError, AuthorizationError
from core.auth import hash_password, verify_password
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

    def signup(
        self,
        email: str,
        name: str,
        password: str,
        max_cash_amt: Optional[float] = None,
        max_cash_pct: Optional[float] = None,
    ) -> dict:
        """Register a new user with a hashed password."""
        normalized_email = self.require_identifier(email, "email").lower()
        normalized_name = self.require_identifier(name, "name")
        if not password or len(password) < 6:
            raise ValidationError("Password must be at least 6 characters.")
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
            "password_hash": hash_password(password),
            "max_cash_amt": max_cash_amt,
            "max_cash_pct": max_cash_pct,
        }
        response = self.client.table(USERS_TABLE).insert(new_user).execute()
        user = response.data[0]
        user.pop("password_hash", None)
        return user

    def authenticate_user(self, email: str, password: str) -> dict:
        """Validate credentials and return the user (without password_hash)."""
        normalized_email = self.require_identifier(email, "email").lower()
        response = (
            self.client.table(USERS_TABLE)
            .select("*")
            .eq("email", normalized_email)
            .limit(1)
            .execute()
        )
        user = self.first_or_none(response)
        if not user or not user.get("password_hash"):
            raise AuthorizationError("Invalid email or password.")
        if not verify_password(password, user["password_hash"]):
            raise AuthorizationError("Invalid email or password.")
        user.pop("password_hash", None)
        return user

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

    def get_user_categories(self, user_id: str) -> list[str]:
        """Return the flat list of wanted categories for a user."""
        user_id = self.require_identifier(user_id, "user_id")
        rows = (
            self.client.table("user_categories")
            .select("category")
            .eq("user_id", user_id)
            .execute()
        ).data
        cats: list[str] = []
        for row in rows:
            for cat in row["category"].split(","):
                cat = cat.strip()
                if cat:
                    cats.append(cat)
        return cats

    def set_user_categories(self, user_id: str, categories: list[str]) -> list[str]:
        """Replace a user's wanted categories (single comma-separated row)."""
        user_id = self.require_identifier(user_id, "user_id")
        self._get_user_or_raise(user_id)
        # Delete existing
        self.client.table("user_categories").delete().eq("user_id", user_id).execute()
        # Insert new row with comma-separated categories
        cleaned = [c.strip() for c in categories if c.strip()]
        if not cleaned:
            return []
        self.client.table("user_categories").insert({
            "user_id": user_id,
            "category": ",".join(cleaned),
        }).execute()
        return cleaned
