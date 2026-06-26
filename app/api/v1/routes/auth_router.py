from fastapi import APIRouter, status, Depends
from sqlmodel import Session
from app.models.user_model import RegisterResponse, UserCreate, LoginRequest
from app.database.postgres import get_session
from app.api.services import auth_service


auth_router = APIRouter()

@auth_router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(req: UserCreate, session:Session = Depends(get_session)):
    return auth_service.register(session, req)


@auth_router.post("/login", status_code=status.HTTP_200_OK, response_model=RegisterResponse)
async def login(req: LoginRequest, session: Session = Depends(get_session)):
    return auth_service.login(session, req)

