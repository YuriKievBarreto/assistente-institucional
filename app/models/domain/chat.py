from dataclasses import dataclass, field
from datetime import datetime
import uuid
from app.models.domain.message import Message


@dataclass
class Chat:
    id: uuid.UUID
    title: str
    user_id: uuid.UUID
    created_at: datetime
    messages: list[Message] = field(default_factory=list)
    deleted_at: datetime | None = None
