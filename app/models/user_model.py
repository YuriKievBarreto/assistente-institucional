from sqlmodel import SQLModel, Field, Relationship
import uuid
from datetime import datetime
from typing import Optional

class User(SQLModel, table= True):
    __tablename__ = "users"
    
    id: uuid.UUID =  Field(default_factory=uuid.uuid4, primary_key=True)

    name: str
    email: str = Field(unique=True)
    avatar_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    deleted_at: Optional[datetime] = None

    accounts: list["UserAccount"] = Relationship(back_populates="user")
    chats: list["Chat"] = Relationship(back_populates="user")



