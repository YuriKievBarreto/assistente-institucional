from fastapi import APIRouter
from app.api.v1.routes.chat_router import router as chat_router
from app.api.v1.routes.user_router import router as user_router
from app.api.v1.routes.auth_router import router as auth_router

api_router = APIRouter()

api_router.include_router(chat_router, prefix="/chat", tags=["Chat"])
api_router.include_router(user_router, prefix="/users", tags=["Users"])
api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
