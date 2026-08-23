from fastapi import APIRouter, Depends, Body, status, HTTPException
from typing import List
from app.models.user_model import User
from app.models.chat_model import ChatMigrateRequest, ChatInputRequest, AIresponse, ChatResponse, Dialogue
from app.chatbot.engine import ChatEngine
from app.dependencies import get_engine, get_current_user, get_current_user_optional
from app.database.postgres import get_session
from app.repositories.chat_repository import find_chats_by_user_id
from fastapi.responses import StreamingResponse


from sqlmodel import Session
from app.services import chat_service

chat_router = APIRouter()


@chat_router.post("/", response_model=StreamingResponse)
async def chat(req: ChatInputRequest, engine: ChatEngine = Depends(get_engine), 
               current_user : User | None = Depends(get_current_user_optional), 
               session: Session = Depends(get_session)) -> StreamingResponse:
    

    return StreamingResponse(
        chat_service.chat_and_save(engine, req, session, current_user),
        media_type="text/plain",
    )


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


@chat_router.get("/", response_model=list[ChatResponse])
async def get_all_chats(session: Session = Depends(get_session),
                        current_user: User = Depends(get_current_user)):
    
    return find_chats_by_user_id(session, current_user.id)
    
