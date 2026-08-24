from sqlmodel import SQLModel
from pydantic import EmailStr
from datetime import datetime
from typing import Optional
import uuid


class UserCreate(SQLModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(SQLModel):
    email: EmailStr
    password: str


class UserResponse(SQLModel):
    id: uuid.UUID
    name: str
    email: str
    avatar_url: Optional[str] = None
    created_at: datetime


class RegisterResponse(SQLModel):
    user: UserResponse
    access_token: str
    token_type: str = "bearer"


TokenResponse = RegisterResponse
