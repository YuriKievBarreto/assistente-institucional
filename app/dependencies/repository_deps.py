from fastapi import Depends
from sqlmodel import Session
from app.database.postgres import get_session
from app.database.qdrant_vector_store import qdrant_client

from app.repositories.interfaces.user_repository_interface import IUserRepository
from app.repositories.interfaces.user_account_repository_interface import IUserAccountRepository
from app.repositories.interfaces.chat_repository_interface import IChatRepository
from app.repositories.interfaces.message_repository_interface import IMessageRepository
from app.repositories.interfaces.vector_repository_interface import VectorRepositoryInterface

from app.repositories.user_repository import UserRepository
from app.repositories.user_account_repository import UserAccountRepository
from app.repositories.chat_repository import ChatRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.qdrant_repository import QdrantRepository


def get_user_repository(session: Session = Depends(get_session)) -> IUserRepository:
    return UserRepository(session=session)


def get_user_account_repository(session: Session = Depends(get_session)) -> IUserAccountRepository:
    return UserAccountRepository(session=session)


def get_chat_repository(session: Session = Depends(get_session)) -> IChatRepository:
    return ChatRepository(session=session)


def get_message_repository(session: Session = Depends(get_session)) -> IMessageRepository:
    return MessageRepository(session=session)


def get_vector_repository() -> VectorRepositoryInterface:
    return QdrantRepository(qdrant_client=qdrant_client, collection_name='ifpb')
