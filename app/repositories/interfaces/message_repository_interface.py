from typing import Protocol
from app.models.message_model import Message, MessageCreate
import uuid


class IMessageRepository(Protocol):
    def create_message(self, message_data: MessageCreate, chat_id: uuid.UUID) -> Message:
        ...