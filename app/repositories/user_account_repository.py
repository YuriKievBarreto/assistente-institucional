from sqlmodel import Session, select
from app.models.user_accounts_model import UserAccountCreate, UserAccount
import uuid
from app.repositories.interfaces.user_account_repository_interface import IUserAccountRepository


class UserAccountRepository(IUserAccountRepository):
    def create_user_account(self, session: Session, user_id: uuid.UUID, user_account_data: UserAccountCreate) -> UserAccount:
        new_user_account = UserAccount(
            user_id=user_id,
            **user_account_data.model_dump()
        )

        session.add(new_user_account)
        session.commit()
        session.refresh(new_user_account)
        return new_user_account

    def find_account_by_user_id(self, session: Session, user_id: uuid.UUID) -> UserAccount | None:
        query = select(UserAccount).where(UserAccount.user_id == user_id)
        return session.exec(query).first()

