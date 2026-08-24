from typing import Protocol
from app.models.domain.user import UserAccount
import uuid


class IUserAccountRepository(Protocol):
    def create_user_account(self, user_id: uuid.UUID, password_hash: str | None) -> UserAccount:
        ...

    def find_account_by_user_id(self, user_id: uuid.UUID) -> UserAccount | None:
        ...