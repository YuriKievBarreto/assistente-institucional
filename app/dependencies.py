from app.chatbot.engine import ChatEngine
from app.models.chat_model import ChatInputRequest
from app.chatbot.rag_logic import RAGConfig, RAGRetriever
from fastapi.security import OAuth2PasswordBearer
from app.core.security import decode_token
from jose import JWTError
from fastapi import HTTPException, Depends, status
from app.models.user_model import User
from app.database.postgres import get_session
from app.chatbot.memory import MemoryManager
from app.repositories import user_repository
from sqlmodel import Session
from app.database.qdrant_vector_store import vector_store
from app.chatbot.models import RAGConfig
from langchain_aws import ChatBedrock

oauth_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
oauth_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

def get_session_id(req: ChatInputRequest) -> str:
    return req.session_id

def get_config() -> RAGConfig:
    return RAGConfig()

def get_retriever() -> RAGRetriever:
    return RAGRetriever(vector_store, get_config())


def get_engine(session_id: str = Depends(get_session_id)) -> ChatEngine:
    memory = MemoryManager(session_id=session_id)
    return ChatEngine(get_retriever(), memory)



def get_current_user(
    token: str = Depends(oauth_scheme),
    session: Session = Depends(get_session)
) -> User:
    

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate":"Bearer"}
    )

    try:
        print(token)
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        
        print(payload)
        if not user_id:
            raise credentials_exception
        
    except JWTError:
        raise credentials_exception
    
    user = user_repository.get_user_by_id(session, user_id)
    print(user)
    if not user:
        raise credentials_exception
    
    return user


def get_current_user_optional( token: str | None = Depends(oauth_scheme_optional),
    session: Session = Depends(get_session)) -> User | None:
        print("tentando verificar se há usuario autorizado")
        if not token:
            print("nenhum access token encontrado")
            return None
        try:
            return get_current_user(token, session)
        except HTTPException:
            return None
        

