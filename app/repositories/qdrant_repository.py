from qdrant_client import QdrantClient
from app.database.qdrant_vector_store import embeddings
from langchain_core.documents import Document
from fastembed import SparseTextEmbedding
from qdrant_client.models import SparseVector, Prefetch, FusionQuery, Fusion
from qdrant_client import QdrantClient
from app.repositories.interfaces.vector_repository_interface import VectorRepositoryInterface

class QdrantRepository(VectorRepositoryInterface):
    def __init__(self, qdrant_client: QdrantClient, collection_name: str = "ifpb"):
          self.qdrant_client = qdrant_client
          self.collection_name = collection_name
          self.sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")


    def hybrid_search(self, query: str, limit: int = 10) -> list[Document]:
        dense_vector = embeddings.embed_query(query)
        sparse_vector = list(self.sparse_model.embed([query]))[0]

        results = self.qdrant_client.query_points(
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
            limit= limit
        )

        return [
                Document(
                    page_content=point.payload["page_content"],
                    metadata={
                        **{k: v for k, v in point.payload.items() if k != "page_content"},
                        "_id": point.id
                    }
                )
                for point in results.points
            ]
        

    def get_parents_by_ids(self, parents_ids: list[str], collection_name: str = "ifpb_parents") -> list[dict]:
        if not parents_ids:
            return []
            
        results = self.qdrant_client.retrieve(
            collection_name=collection_name,
            ids=parents_ids,
            with_payload=True,
        )
        return [point.payload for point in results if point.payload]


    
    