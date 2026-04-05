from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, EmailStr, Field

from typing import Optional, List
from core.auth import get_current_user
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


class UpdateCategoriesRequest(BaseModel):
    categories: List[str] = Field(min_length=1)


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
    def get_user(user_id: str, _: dict = Depends(get_current_user)):
        """Get a user by ID."""
        return user_service.get_user_by_id(user_id)

    @router.get("/email/{email}")
    def get_user_by_email(email: EmailStr, _: dict = Depends(get_current_user)):
        """Look up a user by email address."""
        return user_service.get_user_by_email(str(email))

    @router.patch("/{user_id}")
    def update_user(user_id: str, request: UpdateUserRequest, _: dict = Depends(get_current_user)):
        """Update a user's profile or cash trade limits."""
        return user_service.update_user(
            user_id=user_id,
            name=request.name,
            max_cash_amt=request.max_cash_amt,
            max_cash_pct=request.max_cash_pct,
        )

    @router.delete("/{user_id}")
    def delete_user(user_id: str, _: dict = Depends(get_current_user)):
        """Delete a user account and all associated records."""
        return user_service.delete_user(user_id)

    @router.get("")
    def list_users():
        """List all users (used by frontend guest account selector)."""
        return user_service.list_users()

    @router.get("/{user_id}/categories")
    def get_user_categories(user_id: str, _: dict = Depends(get_current_user)):
        """Get a user's wanted categories."""
        return user_service.get_user_categories(user_id)

    @router.put("/{user_id}/categories")
    def set_user_categories(user_id: str, request: UpdateCategoriesRequest, _: dict = Depends(get_current_user)):
        """Replace a user's wanted categories."""
        return user_service.set_user_categories(user_id, request.categories)

    return router
