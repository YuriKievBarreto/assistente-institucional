from app.models.chat_model import Chat, ChatCreate
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
import uuid

def create_chat(session: Session, chat_info: ChatCreate, user_id: uuid.UUID) -> Chat:
    new_chat = Chat(
        title=chat_info.title,
        user_id=user_id
    )

    
    session.add(new_chat)
    session.commit()
    session.refresh(new_chat)


    return new_chat


def find_chats_by_user_id(session: Session, user_id: uuid.UUID) -> list[Chat]:
    query = (
        select(Chat)
        .where(Chat.user_id == user_id)
        .options(selectinload(Chat.messages))
    )

    chats = list(session.exec(query).all())
    print(chats)

    return chats

def find_chat_by_id(session: Session, chat_id: uuid.UUID) -> Chat | None:
    query = select(Chat).where(Chat.id == chat_id)
    return session.exec(query).first()