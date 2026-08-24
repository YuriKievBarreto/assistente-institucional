from sqlmodel import Session, select
from app.models.user_accounts_model import UserAccountCreate, UserAccount
import uuid
from app.repositories.interfaces.user_account_repository_interface import IUserAccountRepository


class UserAccountRepository(IUserAccountRepository):
    def __init__(self, session: Session):
        self.session = session

    def create_user_account(self, user_id: uuid.UUID, user_account_data: UserAccountCreate) -> UserAccount:
        new_user_account = UserAccount(
            user_id=user_id,
            **user_account_data.model_dump()
        )

        self.session.add(new_user_account)
        self.session.commit()
        self.session.refresh(new_user_account)
        return new_user_account

    def find_account_by_user_id(self, user_id: uuid.UUID) -> UserAccount | None:
        query = select(UserAccount).where(UserAccount.user_id == user_id)
        return self.session.exec(query).first()


