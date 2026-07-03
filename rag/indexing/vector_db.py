from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, SparseVectorParams

vector_db_client = QdrantClient(url="http://localhost:6333")


VECTOR_SIZE = 1024
collection_name = "ifpb"
if not vector_db_client.collection_exists("ifpb"):
    vector_db_client.create_collection(
            collection_name=collection_name,
            vectors_config={
                "dense": VectorParams(
                size=1024,
                distance=Distance.COSINE,
            ),
            },

            sparse_vectors_config={
                "sparse": SparseVectorParams()
            }
        )
    print("Coleção 'ifpb' criada com sucesso!")
else:
    print("Coleção 'ifpb' já existe.")

