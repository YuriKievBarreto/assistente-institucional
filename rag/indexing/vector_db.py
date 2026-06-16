from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from embbedings import embeddings
from qdrant_client.http.models import VectorParams, Distance

vector_db_client = QdrantClient(url="http://localhost:6333")


VECTOR_SIZE = 1024

if not vector_db_client.collection_exists("ifpb"):
    vector_db_client.create_collection(
        collection_name="ifpb",
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
    )
    print("Coleção 'ifpb' criada com sucesso!")
else:
    print("Coleção 'ifpb' já existe.")

