from app.models.message_model import Message, MessageCreate
from app.models.chat_model import Chat
from sqlmodel import Session


def create_message(session: Session, chat_info: ChatCreate, user_id: uuid.UUID) -> Chat:
    new_chat = Chat(
        title=chat_info.title,
        user_id=user_id
    )

    
    session.add(new_chat)
    session.commit()
    session.refresh(new_chat)


    return new_chat