from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional

from service.user_service import UserService


class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str
    max_cash_amt: Optional[float] = None
    max_cash_pct: Optional[float] = None


class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    max_cash_amt: Optional[float] = None
    max_cash_pct: Optional[float] = None


def create_user_routes() -> APIRouter:
    router = APIRouter(prefix="/users", tags=["Users"])

    user_service = UserService()

    @router.post("", status_code=201)
    def create_user(request: CreateUserRequest):
        """Register a new user."""
        try:
            return user_service.create_user(
                email=request.email,
                name=request.name,
                max_cash_amt=request.max_cash_amt,
                max_cash_pct=request.max_cash_pct,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/{user_id}")
    def get_user(user_id: str):
        """Get a user by their ID."""
        try:
            return user_service.get_user_by_id(user_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    @router.get("/email/{email}")
    def get_user_by_email(email: str):
        """Look up a user by email address."""
        try:
            return user_service.get_user_by_email(email)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    @router.patch("/{user_id}")
    def update_user(user_id: str, request: UpdateUserRequest):
        """Update a user's name or cash trade limits."""
        try:
            return user_service.update_user(
                user_id=user_id,
                name=request.name,
                max_cash_amt=request.max_cash_amt,
                max_cash_pct=request.max_cash_pct,
            )
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    @router.delete("/{user_id}")
    def delete_user(user_id: str):
        """Delete a user account."""
        try:
            return user_service.delete_user(user_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    return router