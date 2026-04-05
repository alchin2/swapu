from __future__ import annotations

from supabase import Client

from core.exceptions import NotFoundError, ValidationError
from database.supabase_client import get_supabase_client


class SupabaseService:
    def __init__(self) -> None:
        self._client: Client | None = None

    @property
    def client(self) -> Client:
        if self._client is None:
            self._client = get_supabase_client()
        return self._client

    @staticmethod
    def require_identifier(value: str, field_name: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValidationError(f"{field_name} is required.")
        return normalized

    @staticmethod
    def first_or_raise(response: object, message: str) -> dict:
        data = getattr(response, "data", None)
        if not data:
            raise NotFoundError(message)
        return data[0]

    @staticmethod
    def first_or_none(response: object) -> dict | None:
        data = getattr(response, "data", None)
        if not data:
            return None
        return data[0]