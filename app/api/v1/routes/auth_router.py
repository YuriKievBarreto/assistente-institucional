from fastapi import APIRouter
from app.models.user_model import UserResponse, UserCreate

auth_router = APIRouter()

@auth_router.post("/register", response_model=UserResponse)
async def register(user: UserCreate) -> UserResponse:


    
    return UserResponse()

@auth_router.post("/login")
async def login():
    return "successfully"

