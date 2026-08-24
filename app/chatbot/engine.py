from typing import AsyncGenerator
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import RunnableParallel, RunnableLambda, RunnableSerializable

from app.chatbot.rag_logic import RAGRetriever
from app.chatbot.memory import MemoryManager
from app.chatbot.models import RAGConfig
from app.chatbot.llm import get_groq_llm, get_google_llm, get_bedrock_llm
from app.chatbot.services.formatters import DocumentFormatter
from app.chatbot.prompts import SYSTEM_PROMPT

class ChatEngine:
    def __init__(
        self,
        memory_manager: MemoryManager,
        config: RAGConfig,
        retriever: RAGRetriever,
        llm: BaseChatModel | None = None
    ):
        self.config = config
        self.memory = memory_manager
        self.retriever = retriever
        self.llm = llm or get_bedrock_llm(self.config)
        self.chain = self.build_chain()

    def retrieve_and_format(self, x: dict) -> str:
        docs = self.retriever.multi_query_retrieve(x["question"])
        return DocumentFormatter.format_context_with_metadata(docs)

    def build_chain(self) -> RunnableSerializable:
        return (
            RunnableParallel(
                question=lambda x: x["question"],
                context=RunnableLambda(self.retrieve_and_format),
                chat_history=lambda x: self.memory.get_history()
            )
            | SYSTEM_PROMPT
            | self.llm
        )
        
    def chat(self, question: str) -> str:
        response = self.chain.invoke({"question": question})
        return str(response.content)

    async def stream_chat(self, question: str) -> AsyncGenerator[str, None]:
        async for chunk in self.llm.astream(
            SYSTEM_PROMPT.format_messages(
                question=question,
                context=self.retrieve_and_format({"question": question}),
                chat_history=self.memory.get_history()
            )
        ):
            content = chunk.content
            if isinstance(content, str) and content:
                yield content
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        text_val = part.get("text", "")
                        if text_val:
                            yield text_val