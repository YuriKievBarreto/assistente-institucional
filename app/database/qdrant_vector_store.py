from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from langchain_huggingface import HuggingFaceEndpointEmbeddings

import os
from dotenv import load_dotenv

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")

HF_TOKEN = os.getenv("HF_TOKEN")
EMBEDDING_MODEL_ID = os.getenv("EMBEDDING_MODEL_ID")

qdrant_client = QdrantClient("http://localhost:6333")

embeddings = HuggingFaceEndpointEmbeddings(
    model=EMBEDDING_MODEL_ID,
    huggingfacehub_api_token=HF_TOKEN
)


vector_store = QdrantVectorStore(
    client=qdrant_client,
    collection_name="ifpb",
    embedding=embeddings
)




