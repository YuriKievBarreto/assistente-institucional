from pydantic import BaseModel, Field
from typing import List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class ChatInput(BaseModel):
    query: str
    session_id: str
    
class ChatResponse(BaseModel):
    answer: str


class  RAGConfig(BaseModel):
    k_documents: int = 10
    model_name: str =  "llama-3.1-8b-instant"
    score_threshold: float  = 0.7
    groq_models: dict ={
        "llama_versatille": "llama-3.3-70b-versatile",
        "llama_instant": "llama-3.1-8b-instant",
        "gpt_oss": "openai/gpt-oss-120b"
        
    }
    bedrock_models: dict = {
        "amazon_nova_lite": "amazon.nova-lite-v1:0",
        "claude_haiku_4-5": "global.anthropic.claude-haiku-4-5-20251001-v1:0",
        "amazon_nova_micro": "amazon.nova-micro-v1:0",
        "llama_scout_4": "us.meta.llama4-scout-17b-instruct-v1:0",

    }

    gemini_models: dict = {
    "Gemini3.5Flash": "gemini-3.5-flash",
    "Gemini2.5Pro": "gemini-2.5-pro",
    "Gemini2.5Flash": "gemini-2.5-flash",
    "Gemini2.5FlashLite": "gemini-2.5-flash-lite",
    "Gemini1.5Pro": "gemini-1.5-pro",
    "Gemini1.5Flash": "gemini-1.5-flash"
    }



    use_reranker: bool = True

class QueryList(BaseModel):
    queries: List[str] = Field(max_items=4)