import os
import json
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from rag.chunking.chunking import RAGChunking
from rag.indexing.embbedings import embeddings

from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance
from langchain_qdrant import QdrantVectorStore


def ingest_pipeline(DATALAKE_DIR: str):
    chunker = RAGChunking(datalake_directory=DATALAKE_DIR)

    batch_size = 30
    batch_buffer = []

    client = QdrantClient(url="http://localhost:6333")

    collection_name = "ifpb"

    # Cria a collection apenas se ela não existir
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=1024,
                distance=Distance.COSINE,
            ),
        )

    vectorstore = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
    )

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

            # Envia exatamente lotes de 100
            while len(batch_buffer) >= batch_size:
                lote = batch_buffer[:batch_size]

                print(f"Enviando lote de {len(lote)} chunks ao Qdrant...")

                vectorstore.add_documents(lote)

                batch_buffer = batch_buffer[batch_size:]

    # Envia o restante
    if batch_buffer:
        print(f"Enviando lote final de {len(batch_buffer)} chunks...")
        vectorstore.add_documents(batch_buffer)

    print("Pipeline finalizado com sucesso.")

