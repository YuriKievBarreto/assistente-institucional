import logging
from sentence_transformers import CrossEncoder
from langchain_core.documents import Document
import boto3
from app.core.config import settings

logger = logging.getLogger(__name__)

class Reranker:
    """
    Serviço responsável por re-ordenar (rerank) documentos com base na relevância para a pergunta.
    Suporta estratégia remota via HTTP e estratégia local via CrossEncoder com carregamento sob demanda.
    """
    def __init__(self, use_remote: bool = True):
        self.use_remote = use_remote
        self._local_model = None

    @property
    def local_model(self) -> CrossEncoder:
        """Carrega o modelo pesado apenas sob demanda (Lazy Loading)."""
        if self._local_model is None:
            logger.info("Carregando modelo CrossEncoder localmente (BAAI/bge-reranker-v2-m3)...")
            self._local_model = CrossEncoder("BAAI/bge-reranker-v2-m3", device="cpu", max_length=600)
        return self._local_model

    def rerank(self, query: str, docs: list[Document], top_k: int = 5) -> list[Document]:
        """
        Método principal que executa o rerank utilizando a estratégia configurada (remota ou local).
        """
        if not docs:
            return []

        if self.use_remote:
            return self.remote_rerank(query, docs, top_k)
        return self.local_rerank(query, docs, top_k)

    def remote_rerank(self, query: str, docs: list[Document], top_k: int = 5) -> list[Document]:
        client = boto3.client("bedrock-agent-runtime", region_name="us-east-1", aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,)



        response = client.rerank(
            queries=[
                {
                    "type": "TEXT",
                    "textQuery": {
                        "text": query
                    }
                }
            ],

            sources=[
                {
                    "type": "INLINE",
                    "inlineDocumentSource": {
                        "type": "TEXT",
                        "textDocument": {
                            "text": doc.page_content
                        }
                    }
                } for doc in docs
            ],

            rerankingConfiguration={
                "type": "BEDROCK_RERANKING_MODEL",
                "bedrockRerankingConfiguration": {
                    "modelConfiguration": {
                        "modelArn": (
                            "arn:aws:bedrock:us-east-1::"
                            "foundation-model/cohere.rerank-v3-5:0"
                        )
                    },
                    "numberOfResults": top_k
                }
            }

            
        )        

        return [docs[result["index"]] for result in response["results"]]

    def local_rerank(self, query: str, docs: list[Document], top_k: int = 5) -> list[Document]:
        """Re-ordena os documentos localmente usando o CrossEncoder."""
        pairs = [(query, doc.page_content) for doc in docs]
        scores = self.local_model.predict(pairs)

        ranked = sorted(zip(docs, scores), key=lambda pair: pair[1], reverse=True)
        return [doc for doc, _ in ranked[:top_k]]
