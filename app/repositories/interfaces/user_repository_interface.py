from typing import Protocol
from app.models.domain.user import User
from app.models.schemas.user_schemas import UserCreate
import uuid


class IUserRepository(Protocol):
    def get_user_by_email(self, email: str) -> User | None:
        ...

    def create_user(self, user_data: UserCreate) -> User:
        ...

    def get_user_by_id(self, user_id: str | uuid.UUID) -> User | None:
        ...

    def rollback(self) -> None:
        ...