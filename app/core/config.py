from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "Assistente institucional - IFPB Campus Cajazeiras"
    API_V1_STR: str = "/api/v1"
    
    # Security / JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Databases
    PG_DATABASE_URL: str
    QDRANT_URL: str
    
    # LLM / AI / Embeddings Providers Keys
    GROQ_API_KEY: Optional[str] = None
    GOOGLE_GENAI_API_KEY: Optional[str] = None
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    HF_TOKEN: Optional[str] = None
    
    # Models IDs
    HUGGINGFACE_EMBEDDING_MODEL_ID: Optional[str] = None
    BEDROCK_EMBEDDING_MODEL_ID: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
