from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from app.models.tables.chat_table import ChatTable


class MessageTable(SQLModel, table=True):
    __tablename__ = "messages"

    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    role: str
    content: str
    chat_id: uuid.UUID = Field(foreign_key="chats.id")
    created_at: datetime = Field(default_factory=datetime.now)

    chat: "ChatTable" = Relationship(back_populates="messages")
