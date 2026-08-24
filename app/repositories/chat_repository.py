from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from app.models.tables.chat_table import ChatTable
from app.models.domain.chat import Chat
from app.models.domain.message import Message
from app.repositories.interfaces.chat_repository_interface import IChatRepository
import uuid


class ChatRepository(IChatRepository):
    def __init__(self, session: Session):
        self.session = session

    def _to_entity(self, row: ChatTable) -> Chat:
        return Chat(
            id=row.id,
            title=row.title,
            user_id=row.user_id,
            created_at=row.created_at,
            deleted_at=row.deleted_at,
            messages=[
                Message(
                    id=msg.id,
                    role=msg.role,
                    content=msg.content,
                    chat_id=msg.chat_id,
                    created_at=msg.created_at,
                )
                for msg in (row.messages or [])
            ],
        )

    def create_chat(self, title: str, user_id: uuid.UUID) -> Chat:
        row = ChatTable(title=title, user_id=user_id)
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return self._to_entity(row)

    def find_chats_by_user_id(self, user_id: uuid.UUID) -> list[Chat]:
        query = (
            select(ChatTable)
            .where(ChatTable.user_id == user_id)
            .options(selectinload(ChatTable.messages))
        )
        rows = list(self.session.exec(query).all())
        return [self._to_entity(row) for row in rows]

    def find_chat_by_id(self, chat_id: uuid.UUID) -> Chat | None:
        query = select(ChatTable).where(ChatTable.id == chat_id)
        row = self.session.exec(query).first()
        return self._to_entity(row) if row else None

    def rollback(self) -> None:
        self.session.rollback()
