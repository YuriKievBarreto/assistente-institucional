from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from app.models.tables.message_table import MessageTable
    from app.models.tables.user_table import UserTable


class ChatTable(SQLModel, table=True):
    __tablename__ = "chats"

    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    title: str
    user_id: uuid.UUID = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.now)
    deleted_at: Optional[datetime] = None

    messages: list["MessageTable"] = Relationship(back_populates="chat")
    user: "UserTable" = Relationship(back_populates="chats")
