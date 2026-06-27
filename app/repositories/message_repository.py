from app.models.message_model import Message, MessageCreate
from app.models.chat_model import Chat
from sqlmodel import Session
import uuid


def create_message(session: Session, message_data: MessageCreate, chat_id: uuid.UUID) -> Message:
    new_message = Message(
       role=message_data.role,
       content=message_data.content,
       chat_id=chat_id
    )

    
    session.add(new_message)
    session.commit()
    session.refresh(new_message)


    return new_message