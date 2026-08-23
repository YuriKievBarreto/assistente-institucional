from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_aws import BedrockEmbeddings
import boto3
from app.core.config import settings

bedrock_client = boto3.client(
    "bedrock-runtime",
    region_name=settings.AWS_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)

qdrant_client = QdrantClient(settings.QDRANT_URL)

bedrock_embeddings = BedrockEmbeddings(
    model_id=settings.BEDROCK_EMBEDDING_MODEL_ID,
    client=bedrock_client,
    dimensions=1024
)

hf_embeddings = HuggingFaceEndpointEmbeddings(
    model=settings.HUGGINGFACE_EMBEDDING_MODEL_ID,
    huggingfacehub_api_token=settings.HF_TOKEN
)

embeddings = hf_embeddings

vector_store = QdrantVectorStore(
    client=qdrant_client,
    collection_name="ifpb",
    embedding=embeddings,
    vector_name="dense"
)




