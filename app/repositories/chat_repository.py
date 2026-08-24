from app.models.chat_model import Chat, ChatCreate
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
import uuid
from app.repositories.interfaces.chat_repository_interface import IChatRepository

class ChatRepository(IChatRepository):
    def __init__(self, session: Session):
        self.session = session

    def create_chat(self, chat_info: ChatCreate, user_id: uuid.UUID) -> Chat:
        new_chat = Chat(
            title=chat_info.title,
            user_id=user_id
        )

        self.session.add(new_chat)
        self.session.commit()
        self.session.refresh(new_chat)

        return new_chat

    def find_chats_by_user_id(self, user_id: uuid.UUID) -> list[Chat]:
        query = (
            select(Chat)
            .where(Chat.user_id == user_id)
            .options(selectinload(Chat.messages))
        )

        chats = list(self.session.exec(query).all())
        return chats

    def find_chat_by_id(self, chat_id: uuid.UUID) -> Chat | None:
        query = select(Chat).where(Chat.id == chat_id)
        return self.session.exec(query).first()

    def rollback(self) -> None:
        self.session.rollback()





