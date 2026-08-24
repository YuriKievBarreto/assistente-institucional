from typing import Protocol
from app.models.domain.message import Message
import uuid


class IMessageRepository(Protocol):
    def create_message(self, role: str, content: str, chat_id: uuid.UUID) -> Message:
        ...