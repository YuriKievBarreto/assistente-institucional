from fastapi import APIRouter, status, Depends
from sqlmodel import Session
from app.models.user_model import RegisterResponse, UserCreate, LoginRequest, UserResponse, User
from app.database.postgres import get_session
from app.dependencies import get_current_user
from app.services import auth_service


auth_router = APIRouter()

@auth_router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(req: UserCreate, session:Session = Depends(get_session)):
    return auth_service.register(session, req)


@auth_router.post("/login", status_code=status.HTTP_200_OK, response_model=RegisterResponse)
async def login(req: LoginRequest, session: Session = Depends(get_session)):
    return auth_service.login(session, req)

@auth_router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        name=current_user.name,
        email=current_user.email,
        created_at=current_user.created_at,
        avatar_url=current_user.avatar_url,
        id=current_user.id
    )

