from sqlmodel import SQLModel, Field, Relationship
import uuid
from typing import Optional
from datetime import datetime


class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    chat_id: uuid.UUID = Field(foreign_key="chats.id")

    created_at: datetime = Field(default_factory=datetime.now)
    role: str
    content: str

    chat: "Chat" = Relationship(back_populates="messages")