from fastapi import APIRouter, Depends, Body
from typing import List
from app.chatbot.models import ChatInput, ChatResponse
from app.chatbot.engine import ChatEngine
from app.dependencies import get_engine

chat_router = APIRouter()


@chat_router.post("/", response_model=ChatResponse)
async def chat(req: ChatInput = Body(), engine: ChatEngine = Depends(get_engine)):
    answer = engine.chat(req.query)
    return {"answer": answer}

