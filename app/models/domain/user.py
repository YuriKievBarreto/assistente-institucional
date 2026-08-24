from dataclasses import dataclass
from datetime import datetime
import uuid


@dataclass
class User:
    id: uuid.UUID
    name: str
    email: str
    created_at: datetime
    avatar_url: str | None = None
    deleted_at: datetime | None = None


@dataclass
class UserAccount:
    id: uuid.UUID
    user_id: uuid.UUID
    password_hash: str | None
    created_at: datetime
    deleted_at: datetime | None = None
