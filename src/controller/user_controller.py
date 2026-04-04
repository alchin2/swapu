from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from service.user_service import UserService


class CreateUserRequest(BaseModel):
    email: str
    display_name: str
    avatar_url: Optional[str] = None


class UpdateUserRequest(BaseModel):
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


def create_user_routes() -> APIRouter:
    router = APIRouter(prefix="/users", tags=["Users"])

    user_service = UserService()

    @router.post("", status_code=201)
    def create_user(request: CreateUserRequest):
        """Register a new user."""
        try:
            user = user_service.create_user(
                email=request.email,
                display_name=request.display_name,
                avatar_url=request.avatar_url,
            )
            return user
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
        """Update a user's display name or avatar."""
        try:
            return user_service.update_user(
                user_id=user_id,
                display_name=request.display_name,
                avatar_url=request.avatar_url,
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