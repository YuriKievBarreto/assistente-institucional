from fastapi import APIRouter, Depends, Body
from typing import List
from app.models.chat_model import ChatResponse, ChatInputRequest
from app.chatbot.engine import ChatEngine
from app.dependencies import get_engine
from app.api.services import chat_service

chat_router = APIRouter()


@chat_router.post("/")
async def chat(req: ChatInputRequest, engine: ChatEngine = Depends(get_engine)):
    return chat_service.chat(engine, req)

