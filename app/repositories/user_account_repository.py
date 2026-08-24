from sqlmodel import Session, select
from app.models.tables.user_account_table import UserAccountTable
from app.models.domain.user import UserAccount
from app.repositories.interfaces.user_account_repository_interface import IUserAccountRepository
import uuid


class UserAccountRepository(IUserAccountRepository):
    def __init__(self, session: Session):
        self.session = session

    def _to_entity(self, row: UserAccountTable) -> UserAccount:
        return UserAccount(
            id=row.id,
            user_id=row.user_id,
            password_hash=row.password_hash,
            created_at=row.created_at,
            deleted_at=row.deleted_at,
        )

    def create_user_account(self, user_id: uuid.UUID, password_hash: str | None) -> UserAccount:
        row = UserAccountTable(user_id=user_id, password_hash=password_hash)
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return self._to_entity(row)

    def find_account_by_user_id(self, user_id: uuid.UUID) -> UserAccount | None:
        query = select(UserAccountTable).where(UserAccountTable.user_id == user_id)
        row = self.session.exec(query).first()
        return self._to_entity(row) if row else None
