from fastapi import APIRouter
from app.models.user_model import User

auth_router = APIRouter()

@auth_router.post("/register", response_model=User)
async def register(req: User) -> User:
    return "instancia de user e codigo 204 created"

@auth_router.post("/login")
async def login():
    return "successfully"

