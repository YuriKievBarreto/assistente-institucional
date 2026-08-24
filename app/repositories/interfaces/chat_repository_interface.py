from typing import Protocol
from app.models.chat_model import Chat, ChatCreate
from sqlmodel import Session

import uuid

class IChatRepository(Protocol):
    def create_chat(self, session: Session, chat_info: ChatCreate, user_id: uuid.UUID) -> Chat:
        ...

    def find_chats_by_user_id(self, session: Session, user_id: uuid.UUID) -> list[Chat]:
        ...

    def find_chat_by_id(self, session: Session, chat_id: uuid.UUID) -> Chat | None:
        ...