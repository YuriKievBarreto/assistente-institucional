from sqlmodel import Session, select
from app.models.user_model import UserCreate, User
import uuid

def get_user_by_email(session: Session, email: str) -> User | None:
    query = select(User).where(User.email == email)
    return session.exec(query).first()

def create_user(session: Session, user_data: UserCreate) -> User:
    new_user = User(
        name=user_data.name,
        email=user_data.email
    )

    
    session.add(new_user)
    session.commit()
    session.refresh(new_user)


    return new_user


def get_user_by_id(session: Session, user_id: str | uuid.UUID) -> User | None:
    return session.get(User, uuid.UUID(str(user_id)))