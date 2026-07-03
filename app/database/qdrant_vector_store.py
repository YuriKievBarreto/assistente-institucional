from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_aws import BedrockEmbeddings
import boto3
import os
from dotenv import load_dotenv

load_dotenv()


bedrock_client = boto3.client(
    "bedrock-runtime",
    region_name="us-east-1",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

QDRANT_URL = os.getenv("QDRANT_URL")

HF_TOKEN = os.getenv("HF_TOKEN")
HUGGINGFACE_EMBEDDING_MODEL_ID = os.getenv("HUGGINGFACE_EMBEDDING_MODEL_ID")
BEDROCK_EMBEDDING_MODEL_ID = os.getenv("BEDROCK_EMBEDDING_MODEL_ID")

qdrant_client = QdrantClient(QDRANT_URL)


bedrock_embeddings = BedrockEmbeddings(model_id=BEDROCK_EMBEDDING_MODEL_ID, client=bedrock_client, dimensions=1024)

hf_embeddings = HuggingFaceEndpointEmbeddings(
    model=HUGGINGFACE_EMBEDDING_MODEL_ID,
    huggingfacehub_api_token=HF_TOKEN
)

embeddings = hf_embeddings




vector_store = QdrantVectorStore(
    client=qdrant_client,
    collection_name="ifpb",
    embedding=embeddings,
    vector_name="dense"
)




