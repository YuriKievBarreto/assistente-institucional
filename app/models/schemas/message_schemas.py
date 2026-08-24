from sqlmodel import SQLModel
from datetime import datetime
import uuid


class MessageCreate(SQLModel):
    role: str
    content: str


class MessageResponse(SQLModel):
    id: uuid.UUID
    role: str
    content: str
    created_at: datetime
