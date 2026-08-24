from fastapi import APIRouter, status, Depends
from app.models.schemas.user_schemas import RegisterResponse, TokenResponse, UserCreate, LoginRequest, UserResponse
from app.models.domain.user import User
from app.dependencies import get_current_user, get_auth_service
from app.services.auth_service import AuthService

router = APIRouter()

@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(req: UserCreate, auth_service: AuthService = Depends(get_auth_service)):
    return auth_service.register(req)


@router.post("/login", status_code=status.HTTP_200_OK, response_model=TokenResponse)
async def login(req: LoginRequest, auth_service: AuthService = Depends(get_auth_service)):
    return auth_service.login(req)

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        name=current_user.name,
        email=current_user.email,
        created_at=current_user.created_at,
        avatar_url=current_user.avatar_url,
        id=current_user.id
    )
