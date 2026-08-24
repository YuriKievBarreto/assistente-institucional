from typing import Protocol
from sqlmodel import Session
from app.models.user_model import UserCreate, User
import uuid



class IUserRepository(Protocol):
    def get_user_by_email(self, session: Session, email: str) -> User | None:
        ...

    def create_user(self, session: Session, user_data: UserCreate) -> User:
        ...

    def get_user_by_id(self, session: Session, user_id: str | uuid.UUID) -> User | None:
        ...