import os
from functools import lru_cache

from dotenv import load_dotenv
from supabase import Client, create_client

from core.exceptions import ConfigurationError

load_dotenv()


def _resolve_supabase_url() -> str:
    return os.getenv("SUPABASE_URL", "").rstrip("/")


def _resolve_supabase_key() -> str:
    return os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_DEFAULT") or ""


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    supabase_url = _resolve_supabase_url()
    supabase_key = _resolve_supabase_key()
    if not supabase_url or not supabase_key:
        raise ConfigurationError(
            "Supabase is not configured. Set SUPABASE_URL and SUPABASE_KEY in the environment."
        )
    return create_client(supabase_url, supabase_key)
