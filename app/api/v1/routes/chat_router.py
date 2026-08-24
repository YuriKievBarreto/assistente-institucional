from fastapi import APIRouter, Depends, status, HTTPException
from app.models.user_model import User
from app.models.chat_model import ChatMigrateRequest, ChatInputRequest, ChatResponse
from app.chatbot.engine import ChatEngine
from app.dependencies import get_engine, get_current_user, get_current_user_optional
from app.database.postgres import get_session
from app.repositories.chat_repository import find_chats_by_user_id
from fastapi.responses import StreamingResponse
from sqlmodel import Session
from app.services.chat_service import ChatService

router = APIRouter()


@router.post("/")
async def chat(req: ChatInputRequest, engine: ChatEngine = Depends(get_engine), 
               current_user : User | None = Depends(get_current_user_optional), 
               session: Session = Depends(get_session)) -> StreamingResponse:
    

    return StreamingResponse(
        ChatService.chat_and_save(engine, req, session, current_user),
        media_type="text/plain",
    )


@router.post("/migrate", status_code=status.HTTP_201_CREATED)
async def migrate(req: ChatMigrateRequest, 
                  session: Session = Depends(get_session),
                  current_user: User = Depends(get_current_user)):
   

   try:
        ChatService.migrate_chats(session, req, user_id=current_user.id)
   except Exception:
       session.rollback()
       raise HTTPException(
           status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
           detail="erro ao migrar conversas"
       )


@router.get("/", response_model=list[ChatResponse])
async def get_all_chats(session: Session = Depends(get_session),
                        current_user: User = Depends(get_current_user)) -> list[ChatResponse]:
    
    return ChatService.find_chats_by_user_id(session=session, user_id=current_user.id)
    
