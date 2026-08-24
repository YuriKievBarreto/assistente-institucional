from fastapi import Depends
from app.repositories.interfaces.user_repository_interface import IUserRepository
from app.repositories.interfaces.user_account_repository_interface import IUserAccountRepository
from app.repositories.interfaces.chat_repository_interface import IChatRepository
from app.repositories.interfaces.message_repository_interface import IMessageRepository

from app.dependencies.repository_deps import (
    get_user_repository,
    get_user_account_repository,
    get_chat_repository,
    get_message_repository,
)

from app.services.auth_service import AuthService
from app.services.chat_service import ChatService


def get_auth_service(
    user_repo: IUserRepository = Depends(get_user_repository),
    user_account_repo: IUserAccountRepository = Depends(get_user_account_repository)
) -> AuthService:
    return AuthService(user_repo=user_repo, user_account_repo=user_account_repo)


def get_chat_service(
    chat_repo: IChatRepository = Depends(get_chat_repository),
    message_repo: IMessageRepository = Depends(get_message_repository)
) -> ChatService:
    return ChatService(chat_repo=chat_repo, message_repo=message_repo)
