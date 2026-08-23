from app.chatbot.models import RAGConfig
from langchain_core.vectorstores import VectorStoreRetriever
from qdrant_client import QdrantClient
from app.database.qdrant_vector_store import vector_store
from app.database.qdrant_vector_store import embeddings
from langchain_core.documents import Document
from fastembed import SparseTextEmbedding
from qdrant_client.models import SparseVector, Prefetch, FusionQuery, Fusion
from langchain_classic.retrievers import MultiQueryRetriever
from langchain_core.language_models.chat_models import BaseChatModel
from app.chatbot.models import QueryList
from sentence_transformers import CrossEncoder
from huggingface_hub import InferenceClient
from qdrant_client import QdrantClient
from app.repositories.interfaces.vector_repository_interface import VectorRepositoryInterface
import os
from dotenv import load_dotenv
load_dotenv()

class RAGRetriever:
    def __init__(self, vector_store, config: RAGConfig, llm: BaseChatModel, vector_repo: VectorRepositoryInterface):
        self.vector_repo = vector_repo
        self.vector_store = vector_store
        
        self.config = config
        self.client: QdrantClient = vector_store.client
        self.collection_name: str = vector_store.collection_name
        self.sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")
        self.llm = llm
        self.reranker = None
        self.hf_client = InferenceClient(token=os.getenv("HF_TOKEN"), provider="hf-inference")
        self.debug_mode = False
        if config.use_reranker:
            self.reranker_pesado = CrossEncoder("BAAI/bge-reranker-v2-m3", device="cpu", max_length=600)
            self.reranker = self.reranker_pesado
           
            


    
    def retrieve(self, query: str) -> list[Document]:
       limit = self.config.k_documents
       docs = self.vector_repo.hybrid_search(query=query, limit=limit)

       return [
                doc for doc in docs
                if "sumario" not in doc.metadata.get("Capitulo", "").lower()
                and "sumário" not in doc.metadata.get("Capitulo", "").lower()
            ]

    
    def format_context(self, docs: list[Document]) -> str:
        return "\n\n".join(doc.page_content for doc in docs)
    
    def format_context_with_metadata(self, docs: list[Document]) -> str:
        formatted = []

        allowed_metadata = [
            "titulo_documento",
            "Capitulo",
            "descricao",
            "ano",
            "data_publicacao",
            "url_pagina_referencia",
            "url_arquivo_direto"
        ]

        for doc in docs:
            content = doc.page_content
            meta = doc.metadata or {}

            meta_lines = [
                f"{key}: {meta[key]}"
                for key in allowed_metadata
                if key in meta
            ]

            meta_str = "\n".join(meta_lines)

            formatted.append(
                f"Metadata:\n{meta_str}\n\n"
                f"Context:\n{content}"
            )

               
       

        return "\n\n---\n\n".join(formatted)
    


    def format_for_rerank(self, docs: list[Document]) -> list[Document]:
        formatted = []

        allowed_metadata = [
            "titulo_documento",
            "ano",
            "data_publicacao"
        ]

        for doc in docs:
            content = doc.page_content
            meta = doc.metadata or {}

            meta_lines = [
                f"{key}: {meta[key]}"
                for key in allowed_metadata
                if key in meta
            ]

            meta_str = "\n".join(meta_lines)
            formatted_meta_and_text = self.format_context_with_metadata(docs)

            formatted.append(
                Document(
                    page_content= f"Metadata:\n{meta_str}\n\n"
                f"Context:\n{content}",
                    metadata=meta
                
                )
            )

        
        return formatted

    
    

    
    def generate_queries(self, query: str, k: int = 3):
        prompt = f"""
        Você é um especialista em busca de informações em editais acadêmicos.

        Gere {k} variações da pergunta abaixo para melhorar recuperação em um sistema RAG.

        Regras:
        - retorne no máximo {k} itens
        - nunca gere mais que {k}
        - não explique nada
        - Não responda a pergunta
        - Use linguagem de editais (bolsa, PIBIC, seleção, edital, pesquisa, extensão)
        - Cada query deve ser diferente
        - Foque em intenções diferentes do usuário
        

        Pergunta:
        {query}

        Retorne uma lista com uma query por linha.
        """

        structured_llm = self.llm.with_structured_output(QueryList, method="json_mode")
        response = structured_llm.invoke(prompt)

        return response.queries[:k] 
    

    def _multi_query_retrieve(self, query: str) -> list[Document]:
        queries = self.generate_queries(query)
        queries = [query] + queries
        all_docs = []

        for q in queries:
           docs = self.retrieve(q)
           all_docs.extend(docs)

        unique_docs = self.deduplicate(all_docs)
        top_5_docs = self.remote_rerank(query, unique_docs)
        unique_docs_and_parents = self.resolve_parents_for_docs(top_5_docs)
       

        return unique_docs_and_parents

    def deduplicate(self, docs):
        seen = set()
        unique_docs = []
        for doc in docs:
            key = doc.metadata.get("id") or doc.page_content[:200]

            if key not in seen:
                seen.add(key)
                unique_docs.append(doc)

        return  unique_docs


    def rerank(self, query: str, docs: list[Document], top_k: int=5):
        
        if not docs:
            return []

            
        formatted_docs = self.format_for_rerank(docs)
        
        pairs = [(query, doc.page_content) for doc in formatted_docs]
        scores = self.reranker.predict(pairs)

        ranked = sorted(
            zip(formatted_docs, scores),
            key = lambda pair: pair[1],
            reverse=True
        )

        
        return [doc for doc, score in ranked[:top_k]]
    


    def remote_rerank(self, query: str, docs: list[Document], top_k: int = 5):
        if not docs:
            return []

        api_url="https://qld-familiar-expectations-psp.trycloudflare.com"
        formatted_docs = self.format_for_rerank(docs)
        import requests
        print("rodando reranker localemnte")
        try:
            response = requests.post(
                f"{api_url}/rerank",
                json={
                    "query": query,
                    "docs": [doc.page_content for doc in formatted_docs],
                },
                timeout=30,
            )
            response.raise_for_status()
            scores = response.json()["scores"]
        except requests.RequestException as e:
            print(f"falha ao chamar reranker remoto: {e}")
            return docs[:top_k]  # fallback gracioso

        ranked = sorted(
            zip(formatted_docs, scores),
            key=lambda pair: pair[1],
            reverse=True,
        )

        return [doc for doc, score in ranked[:top_k]]


    def resolve_parent(self, parent_id: str) -> dict | None:
        result = self.client.retrieve(
            collection_name="ifpb_parents",
            ids=[parent_id],
            with_payload=True,
        )
        if result:
            return result[0].payload  # devolve o payload inteiro, não só page_content
        return None
    

    def resolve_parents_for_docs(self, docs: list[Document]) -> list[Document]:
        print("\n========== RESOLVENDO PARENTS ==========")
        print(f"Documentos recebidos: {len(docs)}")

        standalone_docs = []
        parent_ids = []

        seen_parent_ids = set()

        for i, doc in enumerate(docs, start=1):
            parent_id = doc.metadata.get("parent_id")

            # Documento standalone
            if parent_id is None:
                print(f"[{i}] Standalone")
                standalone_docs.append(doc)
                continue

            print(f"[{i}] Child -> parent_id={parent_id}")

            # Child já representado
            if parent_id in seen_parent_ids:
                print(f"    Parent {parent_id} já foi identificado. Ignorando child.")
                continue

            print(f"    Novo parent encontrado: {parent_id}")

            seen_parent_ids.add(parent_id)
            parent_ids.append(parent_id)

        print("\nParents únicos encontrados:")
        for pid in parent_ids:
            print(f" - {pid}")

        parent_docs = []

        print("\nRecuperando parents...")

        for parent_id in parent_ids:
            parent_payload = self.resolve_parent(parent_id)

            if parent_payload is not None:
                parent_docs.append(
                    Document(
                        page_content=parent_payload["page_content"],
                        metadata={
                            **{k: v for k, v in parent_payload.items() if k != "page_content"},
                            "id": parent_id
                        }
                    )
                )

        print("\nResumo:")
        print(f"Standalones: {len(standalone_docs)}")
        print(f"Parents: {len(parent_docs)}")
        print(f"Total retornado: {len(standalone_docs) + len(parent_docs)}")


       

        return standalone_docs + parent_docs
    



