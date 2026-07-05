from langchain_aws import ChatBedrock, ChatBedrockConverse
from app.chatbot.models import RAGConfig
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv()

def get_bedrock_llm(config: RAGConfig, model: str | None =None) -> ChatBedrockConverse:
    model_id = model if model else "claude_haiku_4-5"
    print("inicializando ", model_id)
    return ChatBedrockConverse(
        model=config.bedrock_models[model_id],
        region_name="us-east-1",
        temperature= 0
    )

def get_groq_llm(config: RAGConfig) -> ChatGroq:
    return ChatGroq(
        model=config.groq_models["gpt_oss"],
        api_key=os.getenv("GROQ_API_KEY")
    )