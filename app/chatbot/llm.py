import logging
import os
from dotenv import load_dotenv
from langchain_aws import ChatBedrockConverse
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from app.chatbot.models import RAGConfig

load_dotenv()
logger = logging.getLogger(__name__)

def get_bedrock_llm(config: RAGConfig, model: str | None = None) -> ChatBedrockConverse:
    model_id = model if model else "claude_haiku_4-5"
    if model_id not in config.bedrock_models:
        raise KeyError(f"Modelo '{model_id}' não encontrado em RAGConfig.bedrock_models. Opções: {list(config.bedrock_models.keys())}")
    
    logger.info(f"Inicializando LLM Bedrock com o modelo: {model_id}")
    return ChatBedrockConverse(
        model=config.bedrock_models[model_id],
        region_name="us-east-1",
        temperature=0
    )

def get_groq_llm(config: RAGConfig, model: str | None = None) -> ChatGroq:
    model_id = model if model else "llama_instant"
    if model_id not in config.groq_models:
        raise KeyError(f"Modelo '{model_id}' não encontrado em RAGConfig.groq_models. Opções: {list(config.groq_models.keys())}")
        
    logger.info(f"Inicializando LLM Groq com o modelo: {model_id}")
    return ChatGroq(
        model=config.groq_models[model_id],
        api_key=os.getenv("GROQ_API_KEY")
    )

def get_google_llm(config: RAGConfig, model: str | None = None) -> ChatGoogleGenerativeAI:
    model_id = model if model else "Gemini3.5Flash"
    if model_id not in config.gemini_models:
        raise KeyError(f"Modelo '{model_id}' não encontrado em RAGConfig.gemini_models. Opções: {list(config.gemini_models.keys())}")
        
    logger.info(f"Inicializando LLM Google com o modelo: {model_id}")
    return ChatGoogleGenerativeAI(
        model=config.gemini_models[model_id],
        api_key=os.getenv("GOOGLE_GENAI_API_KEY")
    )
