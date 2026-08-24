from sqlmodel import Session
from fastapi import HTTPException, status
from app.models.user_model import UserCreate, RegisterResponse, TokenResponse, UserResponse, LoginRequest, User
from app.models.user_accounts_model import UserAccountCreate
from app.repositories.interfaces.user_account_repository_interface import IUserAccountRepository
from app.repositories.interfaces.user_repository_interface import IUserRepository
from app.core.security import hash_password, generate_token, verify_password


class AuthService:
    def __init__(self, user_repo: IUserRepository, user_account_repo: IUserAccountRepository):
        self.user_repo = user_repo
        self.user_account_repo = user_account_repo
        

    def register(self, session: Session, user_data: UserCreate) -> RegisterResponse:
        existing_user = self.user_repo.get_user_by_email(session, user_data.email)
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
            new_user = self.user_repo.create_user(session, user_data)
            self.user_account_repo.create_user_account(session, new_user.id, new_user_account_data)
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

    def login(self, session: Session, user_data: LoginRequest) -> TokenResponse:
        db_user: User = self.user_repo.get_user_by_email(session, user_data.email)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="email ou senha incorreto(s)"
            )

        db_user_account = self.user_account_repo.find_account_by_user_id(session, db_user.id)
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

        return TokenResponse(
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





    


    
    

