from sqlmodel import Session
from app.models.tables.message_table import MessageTable
from app.models.domain.message import Message
from app.repositories.interfaces.message_repository_interface import IMessageRepository
import uuid


class MessageRepository(IMessageRepository):
    def __init__(self, session: Session):
        self.session = session

    def _to_entity(self, row: MessageTable) -> Message:
        return Message(
            id=row.id,
            role=row.role,
            content=row.content,
            chat_id=row.chat_id,
            created_at=row.created_at,
        )

    def create_message(self, role: str, content: str, chat_id: uuid.UUID) -> Message:
        row = MessageTable(role=role, content=content, chat_id=chat_id)
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return self._to_entity(row)