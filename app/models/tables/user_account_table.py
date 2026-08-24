from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from app.models.tables.user_table import UserTable


class UserAccountTable(SQLModel, table=True):
    __tablename__ = "user_accounts"

    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    user_id: uuid.UUID = Field(foreign_key="users.id")
    password_hash: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    deleted_at: Optional[datetime] = None

    user: "UserTable" = Relationship(back_populates="accounts")
