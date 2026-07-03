from app.chatbot.models import RAGConfig
from langchain_core.vectorstores import VectorStoreRetriever
from qdrant_client import QdrantClient
from app.database.qdrant_vector_store import vector_store
from app.database.qdrant_vector_store import embeddings
from langchain_core.documents import Document
from fastembed import SparseTextEmbedding
from qdrant_client.models import SparseVector, Prefetch, FusionQuery, Fusion


class RAGRetriever:
    def __init__(self, vector_store, config: RAGConfig):
        self.vector_store = vector_store
        self.config = config
        self.client: QdrantClient = vector_store.client
        self.collection_name: str = vector_store.collection_name
        self.sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")

    
    def retrieve(self, query: str) -> list[Document]:
       dense_vector = embeddings.embed_query(query)
       sparse_vector = list(self.sparse_model.embed([query]))[0]

       results = self.client.query_points(
           collection_name=self.collection_name,
           prefetch=[
               Prefetch(
                   query=dense_vector,
                   using="dense",
                   limit=20
               ),
               Prefetch(
                   query=SparseVector(
                       indices=sparse_vector.indices.tolist(),
                       values=sparse_vector.values.tolist()
                   ),
                   using="sparse",
                   limit=20
               )
           ],
           query=FusionQuery(fusion=Fusion.RRF),
           limit= self.config.k_documents
       )

       docs = [
            Document(
                page_content=point.payload["page_content"],
                metadata={k: v for k, v in point.payload.items() if k != "page_content"}
            )
            for point in results.points
        ]

       return [
           doc for doc in docs
           if "sumário" not in doc.metadata.get("Capitulo", "").lower()
           and "sumario" not in doc.metadata.get("Capitulo", "").lower()
       ]
    
    def format_context(self, docs: list[Document]) -> str:
        print(self.format_context_with_metadata(docs))
        return "\n\n".join(doc.page_content for doc in docs)
    
    def format_context_with_metadata(self, docs: list[Document]) -> str:
        formatted = []
        for doc in docs:
            content = doc.page_content
            meta = doc.metadata or {}
            meta_str = ", ".join(f"{k}: {v}" for k, v in meta.items())
            formatted.append(f"Context:\n{content}\n\nMetadata:\n{meta_str}")
        return "\n\n---\n\n".join(formatted)
    

