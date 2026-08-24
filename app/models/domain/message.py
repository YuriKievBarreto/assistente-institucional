from dataclasses import dataclass
from datetime import datetime
import uuid


@dataclass
class Message:
    id: uuid.UUID
    role: str
    content: str
    chat_id: uuid.UUID
    created_at: datetime
