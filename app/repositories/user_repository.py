from sqlmodel import Session, select
from app.models.tables.user_table import UserTable
from app.models.domain.user import User
from app.models.schemas.user_schemas import UserCreate
from app.repositories.interfaces.user_repository_interface import IUserRepository
import uuid


class UserRepository(IUserRepository):
    def __init__(self, session: Session):
        self.session = session

    def _to_entity(self, row: UserTable) -> User:
        return User(
            id=row.id,
            name=row.name,
            email=row.email,
            avatar_url=row.avatar_url,
            created_at=row.created_at,
            deleted_at=row.deleted_at,
        )

    def get_user_by_email(self, email: str) -> User | None:
        query = select(UserTable).where(UserTable.email == email)
        row = self.session.exec(query).first()
        return self._to_entity(row) if row else None

    def create_user(self, user_data: UserCreate) -> User:
        row = UserTable(name=user_data.name, email=user_data.email)
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return self._to_entity(row)

    def get_user_by_id(self, user_id: str | uuid.UUID) -> User | None:
        row = self.session.get(UserTable, uuid.UUID(str(user_id)))
        return self._to_entity(row) if row else None

    def rollback(self) -> None:
        self.session.rollback()