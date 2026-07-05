from langchain_aws import ChatBedrock
from app.chatbot.models import RAGConfig
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv()

def get_bedrock_llm(config: RAGConfig) -> ChatBedrock:
    return ChatBedrock(
        model=config.bedrock_models["claude_haiku_4-5"],
        region="us-east-1",
        model_kwargs={"temperature": 0},
    )

def get_groq_llm(config: RAGConfig) -> ChatGroq:
    return ChatGroq(
        model=config.groq_models["llama_versatille"],
        api_key=os.getenv("GROQ_API_KEY")
    )