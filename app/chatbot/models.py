from pydantic import BaseModel
from typing import List, Optional

class ChatInput(BaseModel):
    query: str
    session_id: str
    
class ChatResponse(BaseModel):
    answer: str


class RAGConfig(BaseModel):
    k_documents: int = 5
    model_name: str =  "llama-3.1-8b-instant"
    score_threshold: float  = 0.7