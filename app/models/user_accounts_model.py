from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
import uuid
from datetime import datetime

class UserAccount(SQLModel, table=True):
    __tablename__ = "user_accounts"
    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    user_id: uuid.UUID = Field(foreign_key="users.id")
    provider: str
    provider_id: str
    password_hash : Optional[str] = None # só quando o provider é Local
    created_at: datetime = Field(default_factory=datetime.now)

    user : "User" = Relationship(back_populates="accounts")