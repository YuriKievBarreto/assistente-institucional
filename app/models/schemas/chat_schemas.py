from sqlmodel import SQLModel
from datetime import datetime
import uuid
from app.models.schemas.message_schemas import MessageResponse


class ChatMessageHistory(SQLModel):
    role: str
    content: str
    created_at: datetime


class ChatInputRequest(SQLModel):
    query: str
    session_id: str
    history: list[ChatMessageHistory]
    title: str


class ChatResponse(SQLModel):
    id: uuid.UUID
    title: str
    created_at: datetime
    messages: list[MessageResponse] = []


class ChatInstance(SQLModel):
    title: str
    history: list[ChatMessageHistory]
    created_at: datetime


class ChatMigrateRequest(SQLModel):
    chats_data: list[ChatInstance]
