from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_aws import BedrockEmbeddings
import boto3
from functools import lru_cache
from app.core.config import settings

@lru_cache()
def get_qdrant_client() -> QdrantClient:
    return QdrantClient(settings.QDRANT_URL)

@lru_cache()
def get_hf_embeddings() -> HuggingFaceEndpointEmbeddings:
    return HuggingFaceEndpointEmbeddings(
        model=settings.HUGGINGFACE_EMBEDDING_MODEL_ID,
        huggingfacehub_api_token=settings.HF_TOKEN
    )

@lru_cache()
def get_bedrock_embeddings() -> BedrockEmbeddings:
    bedrock_client = boto3.client(
        "bedrock-runtime",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    return BedrockEmbeddings(
        model_id=settings.BEDROCK_EMBEDDING_MODEL_ID,
        client=bedrock_client,
        dimensions=1024
    )

def get_embeddings():
    return get_hf_embeddings()

def get_vector_store(collection_name: str = "ifpb") -> QdrantVectorStore:
    return QdrantVectorStore(
        client=get_qdrant_client(),
        collection_name=collection_name,
        embedding=get_embeddings(),
        vector_name="dense"
    )

# Backward compatibility / Proxy properties if imported directly
qdrant_client = get_qdrant_client()
embeddings = get_embeddings()





