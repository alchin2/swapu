import os
import uuid
from typing import Optional

from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

USERS_TABLE = "users"

class UserService:
    def __init__(self):
        url: str = os.environ["SUPABASE_URL"]
        key: str = os.environ["SUPABASE_KEY"]
        self.client: Client = create_client(url, key)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_user_or_raise(self, user_id: str) -> dict:
        """Return the user row or raise ValueError if not found."""
        response = (
            self.client.table(USERS_TABLE)
            .select("*")
            .eq("id", user_id)
            .maybe_single()
            .execute()
        )
        if response.data is None:
            raise ValueError(f"User '{user_id}' not found.")
        return response.data

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def create_user(
        self,
        email: str,
        display_name: str,
        avatar_url: Optional[str] = None,
    ) -> dict:
        """Create a new user. Raises ValueError if the email is already taken."""
        existing = (
            self.client.table(USERS_TABLE)
            .select("id")
            .eq("email", email)
            .maybe_single()
            .execute()
        )
        if existing.data:
            raise ValueError(f"A user with email '{email}' already exists.")

        new_user = {
            "id": str(uuid.uuid4()),
            "email": email,
            "display_name": display_name,
            "avatar_url": avatar_url,
        }
        response = self.client.table(USERS_TABLE).insert(new_user).execute()
        return response.data[0]

    def get_user_by_id(self, user_id: str) -> dict:
        """Fetch a single user by their UUID."""
        return self._get_user_or_raise(user_id)

    def get_user_by_email(self, email: str) -> dict:
        """Fetch a single user by their email address."""
        response = (
            self.client.table(USERS_TABLE)
            .select("*")
            .eq("email", email)
            .maybe_single()
            .execute()
        )
        if response.data is None:
            raise ValueError(f"No user found with email '{email}'.")
        return response.data

    def update_user(
        self,
        user_id: str,
        display_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> dict:
        """Update mutable fields on an existing user."""
        # Ensure the user exists before attempting an update.
        self._get_user_or_raise(user_id)

        updates: dict = {}
        if display_name is not None:
            updates["display_name"] = display_name
        if avatar_url is not None:
            updates["avatar_url"] = avatar_url

        if not updates:
            # Nothing to change — just return the current record.
            return self._get_user_or_raise(user_id)

        response = (
            self.client.table(USERS_TABLE)
            .update(updates)
            .eq("id", user_id)
            .execute()
        )
        return response.data[0]

    def delete_user(self, user_id: str) -> dict:
        """Delete a user. Raises ValueError if the user does not exist."""
        self._get_user_or_raise(user_id)
        self.client.table(USERS_TABLE).delete().eq("id", user_id).execute()
        return {"message": f"User '{user_id}' deleted successfully."}