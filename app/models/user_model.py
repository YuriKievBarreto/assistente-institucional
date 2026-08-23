from sqlmodel import SQLModel, Field, Relationship
import uuid
from datetime import datetime
from typing import Optional
from pydantic import EmailStr

class UserBase(SQLModel):
    name: str
    email: str



class UserResponse(UserBase):
    id: uuid.UUID
    avatar_url: Optional[str] = None
    created_at: datetime



class UserCreate(UserBase):
    password: str



class User(UserBase, table= True):
    __tablename__ = "users"
    
    id: uuid.UUID =  Field(default_factory=uuid.uuid4, primary_key=True)

    email: EmailStr = Field(unique=True)
    avatar_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    deleted_at: Optional[datetime] = None

    accounts: list["UserAccount"] = Relationship(back_populates="user")
    chats: list["Chat"] = Relationship(back_populates="user")




class RegisterResponse(SQLModel):
    user: UserResponse
    access_token: str
    token_type: str = "bearer"

TokenResponse = RegisterResponse


class LoginRequest(SQLModel):
    email: EmailStr
    password: str