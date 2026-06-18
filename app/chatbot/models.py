from pydantic import BaseModel
from typing import List, Optional

class ChatInput(BaseModel):
    query: str
    session_id: Optional[str]

class ChatResponse(BaseModel):
    answer: str