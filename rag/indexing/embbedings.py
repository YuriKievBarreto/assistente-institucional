import os
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from dotenv import load_dotenv

load_dotenv()


EMBEDDING_MODEL_ID = "BAAI/bge-m3"
HF_TOKEN = os.getenv("HF_TOKEN")

embeddings = HuggingFaceEndpointEmbeddings(
    model="BAAI/bge-m3",
    huggingfacehub_api_token=HF_TOKEN
)

