from sqlmodel import SQLModel, Field, Relationship
import uuid
from app.models.message_model import Message
from typing import Optional
from datetime import datetime

class Chat(SQLModel, table=True):
    __tablename__ = "chats"

    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    user_id: uuid.UUID = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.now)
    title: str
    deleted_at: Optional[datetime] = None


    messages: list["Message"] = Relationship(back_populates="chat")
    user: "User" = Relationship(back_populates="chats")
