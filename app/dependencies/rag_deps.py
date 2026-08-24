from functools import lru_cache
from fastapi import Depends

from app.chatbot.engine import ChatEngine
from app.chatbot.memory import MemoryManager
from app.chatbot.models import RAGConfig
from app.chatbot.rag_logic import RAGRetriever
from app.chatbot.services.query_expander import QueryExpander
from app.chatbot.llm import get_bedrock_llm
from app.models.schemas.chat_schemas import ChatInputRequest
from app.dependencies.repository_deps import get_vector_repository


def get_session_id(req: ChatInputRequest) -> str:
    return req.session_id


def get_config() -> RAGConfig:
    return RAGConfig()


@lru_cache()
def get_retriever() -> RAGRetriever:
    vector_repo = get_vector_repository()
    config = get_config()
    llm = get_bedrock_llm(config, "amazon_nova_lite")
    query_expander = QueryExpander(llm)
    return RAGRetriever(
        config=config,
        llm=llm,
        vector_repo=vector_repo,
        query_expander=query_expander
    )


def get_engine(
    session_id: str = Depends(get_session_id),
    config: RAGConfig = Depends(get_config)
) -> ChatEngine:
    memory = MemoryManager(session_id=session_id)
    return ChatEngine(memory, config, get_retriever())
