from fastapi import APIRouter, Depends, status, HTTPException
from app.models.user_model import User
from app.models.chat_model import ChatMigrateRequest, ChatInputRequest, ChatResponse
from app.chatbot.engine import ChatEngine
from app.dependencies import get_engine, get_current_user, get_current_user_optional, get_chat_service
from fastapi.responses import StreamingResponse
from app.services.chat_service import ChatService

router = APIRouter()


@router.post("/")
async def chat(
    req: ChatInputRequest,
    engine: ChatEngine = Depends(get_engine),
    current_user: User | None = Depends(get_current_user_optional),
    chat_service: ChatService = Depends(get_chat_service)
) -> StreamingResponse:
    return StreamingResponse(
        chat_service.chat_and_save(engine, req, current_user),
        media_type="text/plain",
    )


@router.post("/migrate", status_code=status.HTTP_201_CREATED)
async def migrate(
    req: ChatMigrateRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    try:
        chat_service.migrate_chats(req, user_id=current_user.id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="erro ao migrar conversas"
        )


@router.get("/", response_model=list[ChatResponse])
async def get_all_chats(
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
) -> list[ChatResponse]:
    return chat_service.find_chats_by_user_id(user_id=current_user.id)

    
