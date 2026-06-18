from fastapi import APIRouter
from app.api.v1.routes.chat_router import chat_router

api_router = APIRouter()

api_router.include_router(chat_router, prefix="/chat", tags=["Chat"])