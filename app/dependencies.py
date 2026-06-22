from app.chatbot.engine import ChatEngine
from app.chatbot.models import ChatInput
from app.chatbot.rag_logic import RAGConfig, RAGRetriever
from app.chatbot.memory import MemoryManager
from app.database.qdrant_vector_store import vector_store

from fastapi import Depends


def get_session_id(req: ChatInput) -> str:
    return req.session_id

def get_config() -> RAGConfig:
    return RAGConfig()

def get_retriever() -> RAGRetriever:
    return RAGRetriever(vector_store, get_config())


def get_engine(session_id: str = Depends(get_session_id)) -> ChatEngine:
    memory = MemoryManager(session_id=session_id)
    return ChatEngine(get_retriever(), memory)


    