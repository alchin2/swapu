from fastapi import APIRouter
from pydantic import BaseModel, EmailStr, Field

from core.auth import create_access_token, get_current_user
from service.user_service import UserService
from fastapi import Depends
from typing import Optional


class SignupRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=6, max_length=128)
    max_cash_amt: Optional[float] = Field(default=None, ge=0)
    max_cash_pct: Optional[float] = Field(default=None, ge=0, le=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


def create_auth_routes() -> APIRouter:
    router = APIRouter(prefix="/auth", tags=["Auth"])
    user_service = UserService()

    @router.post("/signup", status_code=201)
    def signup(request: SignupRequest):
        """Register a new user and return a JWT access token."""
        user = user_service.signup(
            email=str(request.email),
            name=request.name,
            password=request.password,
            max_cash_amt=request.max_cash_amt,
            max_cash_pct=request.max_cash_pct,
        )
        token = create_access_token(user["id"], user["name"], user["email"])
        return {"access_token": token, "token_type": "bearer", "user": user}

    @router.post("/login")
    def login(request: LoginRequest):
        """Authenticate and return a JWT access token."""
        user = user_service.authenticate_user(
            email=str(request.email),
            password=request.password,
        )
        token = create_access_token(user["id"], user["name"], user["email"])
        return {"access_token": token, "token_type": "bearer", "user": user}

    @router.get("/me")
    def get_me(current_user: dict = Depends(get_current_user)):
        """Return the current user's profile from the token."""
        user = user_service.get_user_by_id(current_user["sub"])
        user.pop("password_hash", None)
        return user

    return router
