from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, Request

from core.exceptions import AuthorizationError

_JWT_SECRET: str | None = None
_JWT_ALGORITHM = "HS256"
_JWT_EXPIRE_HOURS = 24


def _get_secret() -> str:
    global _JWT_SECRET
    if _JWT_SECRET is None:
        from dotenv import load_dotenv
        load_dotenv()
        _JWT_SECRET = os.getenv("JWT_SECRET", "")
        if not _JWT_SECRET:
            raise AuthorizationError("JWT_SECRET is not configured.")
    return _JWT_SECRET


# --- Password helpers ---

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# --- JWT helpers ---

def create_access_token(user_id: str, name: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "name": name,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=_JWT_EXPIRE_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, _get_secret(), algorithm=_JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, _get_secret(), algorithms=[_JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise AuthorizationError("Token has expired.")
    except jwt.InvalidTokenError:
        raise AuthorizationError("Invalid token.")


# --- FastAPI dependency ---

def get_current_user(request: Request) -> dict:
    """Extract and validate the Bearer token from the Authorization header.
    Returns the decoded JWT payload with keys: sub, name, email."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise AuthorizationError("Missing or invalid Authorization header.")
    token = auth_header[7:]
    return decode_access_token(token)


# Alias for use in Depends()
CurrentUser = Depends(get_current_user)
