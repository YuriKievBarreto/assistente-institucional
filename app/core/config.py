from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path

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

    #DataLake
    ROOT_DIR: Path = Path(__file__).resolve().parents[2]
    LOCAL_DATALAKE_DIR: str
    


    @property
    def DATALAKE_DIR(self) -> Path:
        path = Path(self.LOCAL_DATALAKE_DIR)

        if path.is_absolute():
            return path

        return self.ROOT_DIR / path

    # Crawlers
    LINK_CURSOS_GRADUACAO: str = "https://estudante.ifpb.edu.br/cursos/?cidade=11&nivel_formacao=GRADUACAO"
    LINK_CURSOS_TECNICOS: str = "https://estudante.ifpb.edu.br/cursos/?cidade=11&modalidade=&nome=&formacao=&nivel_formacao=TECNICO&turno=&forma_acesso="
    LINK_CURSOS_POS_GRADUACAO: str = "https://estudante.ifpb.edu.br/cursos/?cidade=11&modalidade=&nome=&formacao=&nivel_formacao=POSGRADUACAO&turno=&forma_acesso="

    BASE_CRAWLERS: str = "https://www.ifpb.edu.br"

    RAIZ_CRAWLER_EDITAIS: str = "/campus/cajazeiras/editais"
    RAIZ_CRAWLER_RESOLUCOES: str = "/campus/cajazeiras/conselho-diretor/resolucoes"
    RAIZ_CRAWLER_PAGINAS: str = "/campus/cajazeiras"
    RAIZ_CRAWLER_REGULAMENTOS: str = "/campus/cajazeiras/ensino/regulamentos/documentos"

    ANO_MINIMO: int = 2026
    ANO_MINIMO_NOTICIAS: int = 2026
    ANO_MINIMO_REGULAMENTOS: int = 2010
    ANO_MINIMO_RESOLUCOES: int = 2025

    @property
    def links_hubs_cursos(self) -> list[str]:
        return [self.LINK_CURSOS_GRADUACAO, self.LINK_CURSOS_TECNICOS, self.LINK_CURSOS_POS_GRADUACAO]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
settings = Settings()

