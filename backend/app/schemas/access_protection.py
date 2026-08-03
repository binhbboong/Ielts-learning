import uuid

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr | None = None
    password: str


class AuthStatusResponse(BaseModel):
    authenticated: bool
    user_id: uuid.UUID | None = None
    email: str | None = None
    display_name: str | None = None


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=120)
