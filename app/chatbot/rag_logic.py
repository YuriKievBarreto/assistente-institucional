from chatbot.models import RAGConfig
from langchain_core.vectorstores import VectorStoreRetriever
from database.qdrant_vector_store import vector_store
from langchain_core.documents import Document


class RAGRetriever:
    def __init__(self, vector_store, config: RAGConfig):
        self.vector_store = vector_store
        self.config = config
        self.retriever: VectorStoreRetriever = self.build_retriever()

    def build_retriever(self) -> VectorStoreRetriever:
        return self.vector_store.as_retriever(
            search_type = "similarity_score_threshold",
            search_kwargs = {"k": self.config.k_documents, "score_threshold": self.config.score_threshold}
        )
    
    def retrieve(self, query: str):
        return self.retriever.invoke(query)
    
    def format_context(self, docs: list[Document]) -> str:
        return "\n\n".join(doc.page_content for doc in docs)
