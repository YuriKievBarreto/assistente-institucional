import os
import json
import sys
from embbedings import embeddings
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from rag.chunking.chunking import RAGChunking

from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance


def ingest_pipeline():
    chunker = RAGChunking(datalake_directory="pdfs_ifpb_completos/editais/invacao")
    batch_size = 100
    batch_buffer = []

    for root, _, files in os.walk("pdfs_ifpb_completos"):
        for file in files:
            if file.endswith(".md"):
                caminho_md = os.path.join(root, file)
                caminho_json = os.path.splitext(caminho_md)[0] + ".json"

                if not os.path.exists(caminho_json):
                    print(f"JSON não encontrado para: {file}, pulando...")
                    continue

                # ... lógica de leitura do chunk ...

                with open(caminho_json, "r", encoding="utf-8") as f:
                        meta = json.load(f)

                chunks = list(chunker.chunk_content(caminho_md, meta))
                batch_buffer.extend(chunks)

            # Quando atingir o tamanho do lote, envia e limpa a memória
            if len(batch_buffer) >= batch_size:
                print(f"Enviando lote de {len(batch_buffer)} chunks ao Qdrant...")
                QdrantVectorStore.from_documents(
                            documents=batch_buffer,
                            embedding=embeddings,
                            url="http://localhost:6333",
                            collection_name="ifpb",
                            vector_params=VectorParams(size=768, distance=Distance.COSINE),
                            force_recreate=False
                        )
                batch_buffer = [] # Libera a RAM

    # Envia o que sobrou (se o resto for menor que o batch_size)
    if batch_buffer:
        QdrantVectorStore.from_documents(
                            documents=batch_buffer,
                            embedding=embeddings,
                            url="http://localhost:6333",
                            collection_name="ifpb",
                            force_recreate=True
                        )

ingest_pipeline()