from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from app.core.security import decode_token
from app.models.domain.user import User
from app.repositories.interfaces.user_repository_interface import IUserRepository
from app.dependencies.repository_deps import get_user_repository

oauth_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
oauth_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    token: str = Depends(oauth_scheme),
    user_repo: IUserRepository = Depends(get_user_repository)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = user_repo.get_user_by_id(user_id)
    if not user:
        raise credentials_exception

    return user


def get_current_user_optional(
    token: str | None = Depends(oauth_scheme_optional),
    user_repo: IUserRepository = Depends(get_user_repository)
) -> User | None:
    if not token:
        return None
    try:
        return get_current_user(token, user_repo)
    except HTTPException:
        return None
