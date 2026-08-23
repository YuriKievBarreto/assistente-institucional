from sqlmodel import Session
from fastapi import HTTPException, status
from app.models.user_model import UserCreate, RegisterResponse, UserResponse, LoginRequest, User
from app.models.user_accounts_model import UserAccountCreate
from app.repositories import user_repository, user_account_repository
from app.core.security import hash_password, generate_token, verify_password


def register(session: Session, user_data: UserCreate) -> RegisterResponse:
    existing_user = user_repository.get_user_by_email(session, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email já cadastrado"
        )
    
    new_user_account_data = UserAccountCreate(
            provider= "local",
            provider_id=user_data.email,
            password_hash=hash_password(user_data.password)

        )

    try:
        new_user = user_repository.create_user(session, user_data)
        user_account_repository.create_user_account(session, new_user.id, new_user_account_data)
    except Exception:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="erro ao criar conta"
        )

    token = generate_token(str(new_user.id))

    return RegisterResponse(
        user= UserResponse(
            name=new_user.name,
            email=new_user.email,
            id= new_user.id,
            avatar_url= new_user.avatar_url,
            created_at=new_user.created_at
        ),
        access_token=token,
        token_type="bearer"
    )


def login(session: Session, user_data: LoginRequest) -> RegisterResponse:
    db_user: User = user_repository.get_user_by_email(session, user_data.email)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="email ou senha incorreto(s)"
        )

    db_user_account = user_account_repository.find_account_by_user_id(session, db_user.id)
    if not db_user_account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="email ou senha incorreto(s)"
        )

    if not verify_password(user_data.password, db_user_account.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="email ou senha incorreto(s)"
        )
    
    token = generate_token(str(db_user.id))

    return RegisterResponse(
        user=UserResponse(
            id=db_user.id,
            name=db_user.name,
            email=db_user.email,
            avatar_url=db_user.avatar_url,
            created_at=db_user.created_at
        ),
        access_token=token,
        token_type="bearer"
    )

    


    
    

