from sqlmodel import SQLModel, Field, Relationship
from pydantic import EmailStr
from datetime import datetime
from typing import Optional, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from app.models.tables.user_account_table import UserAccountTable
    from app.models.tables.chat_table import ChatTable


class UserTable(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    email: EmailStr = Field(unique=True)
    avatar_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    deleted_at: Optional[datetime] = None

    accounts: list["UserAccountTable"] = Relationship(back_populates="user")
    chats: list["ChatTable"] = Relationship(back_populates="user")
