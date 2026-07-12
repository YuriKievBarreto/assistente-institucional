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

PARENTS_SUFFIX = "_parents"
DUMMY_VECTOR_SIZE = 2  


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


def enviar_batch_parents(client: QdrantClient, parents_collection_name: str, parents: list) -> None:
   
    if not parents:
        return

    points = []
    for parent in parents:
        parent_id = parent.metadata["parent_id"]
        points.append(PointStruct(
            id=parent_id,  
            vector={"dummy": [0.0] * DUMMY_VECTOR_SIZE},
            payload={
                "page_content": parent.page_content,
                **parent.metadata
            }
        ))

    client.upsert(collection_name=parents_collection_name, points=points)
    print(f"  -> {len(points)} parents enviados para '{parents_collection_name}'.")


def ingest_pipeline(DATALAKE_DIR: str):
    chunker = RAGChunking(datalake_directory=DATALAKE_DIR)

    batch_size = 64
    batch_buffer = []       
    parents_buffer = []     

    client = QdrantClient(url="http://localhost:6333")
    collection_name = "ifpb"
    parents_collection_name = f"{collection_name}{PARENTS_SUFFIX}"

    if client.collection_exists(collection_name):
        client.delete_collection(collection_name)
        print("Coleção existente removida.")

    if client.collection_exists(parents_collection_name):
        client.delete_collection(parents_collection_name)
        print("Coleção de parents existente removida.")

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
    print("Coleção principal criada com suporte a vetores densos e esparsos.")

    client.create_collection(
        collection_name=parents_collection_name,
        vectors_config={
            "dummy": VectorParams(
                size=DUMMY_VECTOR_SIZE,
                distance=Distance.COSINE,
            )
        },
    )
    print("Coleção de parents criada (sem busca vetorial real, apenas lookup por ID).")

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

            
            novos_parents = [c for c in chunks if c.metadata.get("chunk_type") == "parent"]
            novos_children = [c for c in chunks if c.metadata.get("chunk_type") != "parent"]

            parents_buffer.extend(novos_parents)
            batch_buffer.extend(novos_children)

            while len(batch_buffer) >= batch_size:
                lote = batch_buffer[:batch_size]
                print(f"Enviando lote de {len(lote)} chunks ao Qdrant...")
                enviar_batch(client, collection_name, lote)
                batch_buffer = batch_buffer[batch_size:]

    if batch_buffer:
        print(f"Enviando lote final de {len(batch_buffer)} chunks...")
        enviar_batch(client, collection_name, batch_buffer)

    
    
    if parents_buffer:
        print(f"Enviando {len(parents_buffer)} parents ao Qdrant...")
        enviar_batch_parents(client, parents_collection_name, parents_buffer)

    print("Pipeline finalizado com sucesso.")