from app.chatbot.models import RAGConfig
from langchain_core.vectorstores import VectorStoreRetriever
from app.database.qdrant_vector_store import vector_store
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
        print(self.format_context_with_metadata(docs))
        return "\n\n".join(doc.page_content for doc in docs)
    
    def format_metadata(self, docs: list[Document]) -> str:
        formated_docs = []
        for doc in docs:
            meta = doc.metadata or {}

            meta_str = ", ".join(
                f"{key}: {value}" for key, value in meta.items()
            )

            formated_docs.append(f"[{meta_str}]")

        return "\n\n".join(formated_docs)
    
    def format_context_with_metadata(self, docs: list[Document]) -> str:
        formatted = []

        for doc in docs:
            content = doc.page_content
            meta = doc.metadata or {}

            meta_str = ", ".join(f"{k}: {v}" for k, v in meta.items())

            formatted.append(
                f"Context:\n{content}\n\nMetadata:\n{meta_str}"
            )

        print("\n\n---\n\n".join(formatted))
        return "\n\n---\n\n".join(formatted)
    

