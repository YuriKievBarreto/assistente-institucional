from fastapi import APIRouter
from app.api.v1.routes.chat_router import chat_router
from app.api.v1.routes.user_router import user_router

api_router = APIRouter()

api_router.include_router(chat_router, prefix="/chat", tags=["Chat"])
api_router.include_router(user_router, prefix="/users", tags=["Users"])
api_router.include_router(user_router, prefix="/auth", tags=["Auth"])
