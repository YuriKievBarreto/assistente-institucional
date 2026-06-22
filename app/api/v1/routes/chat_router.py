from fastapi import APIRouter
from app.chatbot.models import ChatInput, ChatResponse
chat_router = APIRouter()

@chat_router.post("/", response_model=ChatResponse)
async def test(req: ChatInput):

    return {"answer": f"you said: {req.query}"}
