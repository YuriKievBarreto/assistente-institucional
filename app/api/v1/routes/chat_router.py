from fastapi import APIRouter, Depends, Body, status, HTTPException
from typing import List
from app.models.user_model import User
from app.models.chat_model import ChatMigrateRequest, ChatInputRequest
from app.chatbot.engine import ChatEngine
from app.dependencies import get_engine, get_current_user
from app.database.postgres import get_session

from sqlmodel import Session
from app.api.services import chat_service

chat_router = APIRouter()


@chat_router.post("/")
async def chat(req: ChatInputRequest, engine: ChatEngine = Depends(get_engine)):
    return chat_service.chat(engine, req)



@chat_router.post("/migrate", status_code=status.HTTP_201_CREATED)
async def migrate(req: ChatMigrateRequest, 
                  session: Session = Depends(get_session),
                  current_user: User = Depends(get_current_user)):
   

   try:
        chat_service.migrate_chats(session, req, user_id=current_user.id)
   except Exception:
       session.rollback()
       raise HTTPException(
           status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
           detail="erro ao migrar conversas"
       )


