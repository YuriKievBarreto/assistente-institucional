from sqlmodel import Session, select
from app.models.user_model import UserCreate, User
import uuid
from app.repositories.interfaces.user_repository_interface import IUserRepository


class UserRepository(IUserRepository):
    def __init__(self, session: Session):
        self.session = session

    def get_user_by_email(self, email: str) -> User | None:
        query = select(User).where(User.email == email)
        return self.session.exec(query).first()

    def create_user(self, user_data: UserCreate) -> User:
        new_user = User(
            name=user_data.name,
            email=user_data.email
        )

        self.session.add(new_user)
        self.session.commit()
        self.session.refresh(new_user)

        return new_user

    def get_user_by_id(self, user_id: str | uuid.UUID) -> User | None:
        return self.session.get(User, uuid.UUID(str(user_id)))

    def rollback(self) -> None:
        self.session.rollback()

