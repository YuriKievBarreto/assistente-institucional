import requests
import logging
from sentence_transformers import CrossEncoder
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

class Reranker:
    """
    Serviço responsável por re-ordenar (rerank) documentos com base na relevância para a pergunta.
    Suporta estratégia remota via HTTP e estratégia local via CrossEncoder com carregamento sob demanda.
    """
    def __init__(self, use_remote: bool = True, remote_url: str = None):
        self.use_remote = use_remote
        self.remote_url = remote_url or "https://qld-familiar-expectations-psp.trycloudflare.com"
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
        """Re-ordena os documentos fazendo uma requisição ao servidor de rerank remoto."""
        try:
            response = requests.post(
                f"{self.remote_url}/rerank",
                json={
                    "query": query,
                    "docs": [doc.page_content for doc in docs],
                },
                timeout=30,
            )
            response.raise_for_status()
            scores = response.json()["scores"]

            ranked = sorted(zip(docs, scores), key=lambda pair: pair[1], reverse=True)
            return [doc for doc, _ in ranked[:top_k]]
            
        except Exception as e:
            logger.warning(f"Falha ao chamar reranker remoto ({e}). Aplicando fallback gracioso.")
            return docs[:top_k]

    def local_rerank(self, query: str, docs: list[Document], top_k: int = 5) -> list[Document]:
        """Re-ordena os documentos localmente usando o CrossEncoder."""
        pairs = [(query, doc.page_content) for doc in docs]
        scores = self.local_model.predict(pairs)

        ranked = sorted(zip(docs, scores), key=lambda pair: pair[1], reverse=True)
        return [doc for doc, _ in ranked[:top_k]]
