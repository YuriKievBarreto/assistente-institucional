from typing import Protocol
from app.models.message_model import Message, MessageCreate
from sqlmodel import Session
import uuid


class IMessageRepository(Protocol):
    def create_message(self, session: Session, message_data: MessageCreate, chat_id: uuid.UUID) -> Message:
        ...