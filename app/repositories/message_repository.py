from app.models.message_model import Message, MessageCreate
from app.models.chat_model import Chat
from sqlmodel import Session
import uuid
from app.repositories.interfaces.message_repository_interface import IMessageRepository


class MessageRepository(IMessageRepository):
    def __init__(self, session: Session):
        self.session = session

    def create_message(self, message_data: MessageCreate, chat_id: uuid.UUID) -> Message:
        new_message = Message(
           role=message_data.role,
           content=message_data.content,
           chat_id=chat_id
        )

        self.session.add(new_message)
        self.session.commit()
        self.session.refresh(new_message)

        return new_message
