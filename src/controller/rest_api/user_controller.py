from fastapi import APIRouter, status
from pydantic import BaseModel, EmailStr, Field

from typing import Optional
from service.user_service import UserService


class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=120)
    max_cash_amt: Optional[float] = Field(default=None, ge=0)
    max_cash_pct: Optional[float] = Field(default=None, ge=0, le=100)


class UpdateUserRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    max_cash_amt: Optional[float] = Field(default=None, ge=0)
    max_cash_pct: Optional[float] = Field(default=None, ge=0, le=100)


def create_user_routes() -> APIRouter:
    router = APIRouter(prefix="/users", tags=["Users"])
    user_service = UserService()

    @router.post("", status_code=status.HTTP_201_CREATED)
    def create_user(request: CreateUserRequest):
        """Register a new user."""
        return user_service.create_user(
            email=str(request.email),
            name=request.name,
            max_cash_amt=request.max_cash_amt,
            max_cash_pct=request.max_cash_pct,
        )

    @router.get("/{user_id}")
    def get_user(user_id: str):
        """Get a user by ID."""
        return user_service.get_user_by_id(user_id)

    @router.get("/email/{email}")
    def get_user_by_email(email: EmailStr):
        """Look up a user by email address."""
        return user_service.get_user_by_email(str(email))

    @router.patch("/{user_id}")
    def update_user(user_id: str, request: UpdateUserRequest):
        """Update a user's profile or cash trade limits."""
        return user_service.update_user(
            user_id=user_id,
            name=request.name,
            max_cash_amt=request.max_cash_amt,
            max_cash_pct=request.max_cash_pct,
        )

    @router.delete("/{user_id}")
    def delete_user(user_id: str):
        """Delete a user account and all associated records."""
        return user_service.delete_user(user_id)

    @router.get("")
    def list_users():
        """List all users (used by frontend guest account selector)."""
        return user_service.list_users()

    return router
