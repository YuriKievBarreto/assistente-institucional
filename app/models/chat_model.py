from sqlmodel import SQLModel, Field, Relationship
import uuid
from typing import Optional
from datetime import datetime

class ChatBase(SQLModel):
    title: str



class ChatCreate(ChatBase):
    pass



class ChatResponse(ChatBase):
   id: uuid.UUID
   user_id: uuid.UUID
   created_at: datetime



class Chat(ChatBase, table=True):
    __tablename__ = "chats"

    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    user_id: uuid.UUID = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.now)
    deleted_at: Optional[datetime] = None


    messages: list["Message"] = Relationship(back_populates="chat")
    user: "User" = Relationship(back_populates="chats")
