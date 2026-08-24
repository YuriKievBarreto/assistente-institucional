import logging
from langchain_aws import ChatBedrockConverse
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from app.chatbot.models import RAGConfig
from app.core.config import settings

logger = logging.getLogger(__name__)

def get_bedrock_llm(config: RAGConfig, model: str | None = None) -> ChatBedrockConverse:
    model_id = model if model else "amazon_nova_lite"
    if model_id not in config.bedrock_models:
        raise KeyError(f"Modelo '{model_id}' não encontrado em RAGConfig.bedrock_models. Opções: {list(config.bedrock_models.keys())}")
    
    logger.info(f"Inicializando LLM Bedrock com o modelo: {model_id}")
    return ChatBedrockConverse(
        model=config.bedrock_models[model_id],
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        temperature=0
    )

def get_groq_llm(config: RAGConfig, model: str | None = None) -> ChatGroq:
    model_id = model if model else "llama_versatille"
    if model_id not in config.groq_models:
        raise KeyError(f"Modelo '{model_id}' não encontrado em RAGConfig.groq_models. Opções: {list(config.groq_models.keys())}")
        
    logger.info(f"Inicializando LLM Groq com o modelo: {model_id}")
    return ChatGroq(
        model=config.groq_models[model_id],
        api_key=settings.GROQ_API_KEY
    )

def get_google_llm(config: RAGConfig, model: str | None = None) -> ChatGoogleGenerativeAI:
    model_id = model if model else "Gemini3.5Flash"
    if model_id not in config.gemini_models:
        raise KeyError(f"Modelo '{model_id}' não encontrado em RAGConfig.gemini_models. Opções: {list(config.gemini_models.keys())}")
        
    logger.info(f"Inicializando LLM Google com o modelo: {model_id}")
    return ChatGoogleGenerativeAI(
        model=config.gemini_models[model_id],
        api_key=settings.GOOGLE_GENAI_API_KEY
    )
