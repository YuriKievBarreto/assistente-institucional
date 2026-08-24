from typing import Protocol
from sqlmodel import Session 
from app.models.user_accounts_model import UserAccountCreate, UserAccount
import uuid




class IUserAccountRepository(Protocol):
    def create_user_account(self, session: Session, user_id: uuid.UUID, user_account_data: UserAccountCreate) -> UserAccount:
        ...

    def find_account_by_user_id(self, session: Session, user_id: uuid.UUID) -> UserAccount | None:
        ...