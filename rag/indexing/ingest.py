import os
import json
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from rag.chunking.chunking import RAGChunking
from rag.indexing.embbedings import embeddings
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, SparseVector
from qdrant_client.http.models import VectorParams, Distance, SparseVectorParams

from fastembed import SparseTextEmbedding

sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")



def enviar_batch(client: QdrantClient, collection_name: str, chunks: list) -> None:
    texts = [chunk.page_content for chunk in chunks]

    dense_vectors = embeddings.embed_documents(texts)
    sparse_vectors = list(sparse_model.embed(texts))

    points = []
    for chunk, dense, sparse in zip(chunks, dense_vectors, sparse_vectors):
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector={
                "dense": dense,
                "sparse": SparseVector(
                    indices=sparse.indices.tolist(),
                    values=sparse.values.tolist()
                )
            },
            payload={
                "page_content": chunk.page_content,
                **chunk.metadata
            }
        ))

    client.upsert(collection_name=collection_name, points=points)


def ingest_pipeline(DATALAKE_DIR: str):
    chunker = RAGChunking(datalake_directory=DATALAKE_DIR)

    batch_size = 30
    batch_buffer = []

    client = QdrantClient(url="http://localhost:6333")
    collection_name = "ifpb"

    if client.collection_exists(collection_name):
        client.delete_collection(collection_name)
        print("Coleção existente removida.")

    client.create_collection(
        collection_name=collection_name,
        vectors_config={
            "dense": VectorParams(
                size=1024,
                distance=Distance.COSINE,
            )
        },
        sparse_vectors_config={
            "sparse": SparseVectorParams()
        }
    )
    print("Coleção criada com suporte a vetores densos e esparsos.")

    for root, _, files in os.walk(DATALAKE_DIR):
        for file in files:
            if not file.endswith(".md"):
                continue

            caminho_md = os.path.join(root, file)
            caminho_json = os.path.splitext(caminho_md)[0] + ".json"

            if not os.path.exists(caminho_json):
                print(f"JSON não encontrado para: {file}, pulando...")
                continue

            with open(caminho_json, "r", encoding="utf-8") as f:
                meta = json.load(f)

            chunks = list(chunker.chunk_content(caminho_md, meta))
            batch_buffer.extend(chunks)

            while len(batch_buffer) >= batch_size:
                lote = batch_buffer[:batch_size]
                print(f"Enviando lote de {len(lote)} chunks ao Qdrant...")
                enviar_batch(client, collection_name, lote)
                batch_buffer = batch_buffer[batch_size:]

    if batch_buffer:
        print(f"Enviando lote final de {len(batch_buffer)} chunks...")
        enviar_batch(client, collection_name, batch_buffer)

    print("Pipeline finalizado com sucesso.")

