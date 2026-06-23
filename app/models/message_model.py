from sqlmodel import SQLModel, Field, Relationship
import uuid
from datetime import datetime


class MessageBase(SQLModel):
    role: str
    content: str

    


class MessageCreate(MessageBase):
    pass

   
class MessageResponse(MessageBase):
    id: uuid.UUID 
    chat_id: uuid.UUID
    created_at: datetime 




class Message(MessageBase, table=True):
    __tablename__ = "messages"

    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    chat_id: uuid.UUID = Field(foreign_key="chats.id")

    created_at: datetime = Field(default_factory=datetime.now)

    chat: "Chat" = Relationship(back_populates="messages")