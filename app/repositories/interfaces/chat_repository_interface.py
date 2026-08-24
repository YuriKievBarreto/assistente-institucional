from typing import Protocol
from app.models.domain.chat import Chat
import uuid


class IChatRepository(Protocol):
    def create_chat(self, title: str, user_id: uuid.UUID) -> Chat:
        ...

    def find_chats_by_user_id(self, user_id: uuid.UUID) -> list[Chat]:
        ...

    def find_chat_by_id(self, chat_id: uuid.UUID) -> Chat | None:
        ...

    def rollback(self) -> None:
        ...