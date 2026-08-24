from app.chatbot.models import RAGConfig
from langchain_core.documents import Document
from langchain_core.language_models.chat_models import BaseChatModel
from app.chatbot.services.query_expander import QueryExpander
from app.chatbot.services.reranker import Reranker
from app.repositories.interfaces.vector_repository_interface import VectorRepositoryInterface

from concurrent.futures import ThreadPoolExecutor

class RAGRetriever:
    def __init__(
        self, 
        config: RAGConfig, 
        llm: BaseChatModel, 
        vector_repo: VectorRepositoryInterface, 
        query_expander: QueryExpander,
        reranker: Reranker = None
    ):
        self.vector_repo = vector_repo
        self.config = config
        self.llm = llm
        self.query_expander = query_expander
        self.reranker = reranker or Reranker(use_remote=True)

    def retrieve(self, query: str) -> list[Document]:
       limit = self.config.k_documents
       docs = self.vector_repo.hybrid_search(query=query, limit=limit)

       return [
            doc for doc in docs
            if "sumario" not in doc.metadata.get("Capitulo", "").lower()
            and "sumário" not in doc.metadata.get("Capitulo", "").lower()
        ]

    def multi_query_retrieve(self, query: str) -> list[Document]:
        queries = self.query_expander.expand(query, k=3)
        all_docs = []

        with ThreadPoolExecutor(max_workers=len(queries)) as executor:
            results = list(executor.map(self.retrieve, queries))
            for docs in results:
                all_docs.extend(docs)

        unique_docs = self.deduplicate(all_docs)
        top_5_docs = self.reranker.rerank(query, unique_docs, top_k=5)
        return self.resolve_parents_for_docs(top_5_docs)

    def deduplicate(self, docs: list[Document]) -> list[Document]:
        seen = set()
        unique_docs = []
        for doc in docs:
            key = doc.metadata.get("id") or doc.page_content[:200]

            if key not in seen:
                seen.add(key)
                unique_docs.append(doc)

        return unique_docs

    def resolve_parents_for_docs(self, docs: list[Document]) -> list[Document]:
        standalone_docs = [doc for doc in docs if doc.metadata.get("parent_id") is None]
        
        seen_parent_ids = set()
        parent_ids = []

        for doc in docs:
            parent_id = doc.metadata.get("parent_id")
            if parent_id and parent_id not in seen_parent_ids:
                seen_parent_ids.add(parent_id)
                parent_ids.append(parent_id)

        parent_docs = self.vector_repo.get_parents_by_ids(parent_ids)
        return standalone_docs + parent_docs
    



