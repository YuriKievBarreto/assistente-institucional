from sqlmodel import Session, select
from app.models.user_accounts_model import UserAccountCreate, UserAccount
import uuid


def create_user_account(session: Session, user_id: uuid.UUID, user_account_data: UserAccountCreate):
    new_user_account = UserAccount(
        user_id = user_id,
        **user_account_data.model_dump()
    )

    session.add(new_user_account)
    session.commit()
    session.refresh(new_user_account)
    return new_user_account