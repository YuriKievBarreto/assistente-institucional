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

class RAGRetriever:
    def __init__(self, vector_store, config: RAGConfig, llm: BaseChatModel):
        self.vector_store = vector_store
        self.config = config
        self.client: QdrantClient = vector_store.client
        self.collection_name: str = vector_store.collection_name
        self.sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")
        self.llm = llm

    
    def retrieve(self, query: str) -> list[Document]:
       dense_vector = embeddings.embed_query(query)
       sparse_vector = list(self.sparse_model.embed([query]))[0]

       results = self.client.query_points(
           collection_name=self.collection_name,
           prefetch=[
               Prefetch(
                   query=dense_vector,
                   using="dense",
                   limit=20
               ),
               Prefetch(
                   query=SparseVector(
                       indices=sparse_vector.indices.tolist(),
                       values=sparse_vector.values.tolist()
                   ),
                   using="sparse",
                   limit=20
               )
           ],
           query=FusionQuery(fusion=Fusion.RRF),
           limit= self.config.k_documents
       )

       docs = [
            Document(
                page_content=point.payload["page_content"],
                metadata={
                    **{k: v for k, v in point.payload.items() if k != "page_content"},
                    "_id": point.id  # 👈 importante
                },
                
            )
            for point in results.points
        ]

       return [
           doc for doc in docs
           if "sumário" not in doc.metadata.get("Capitulo", "").lower()
           and "sumario" not in doc.metadata.get("Capitulo", "").lower()
       ]
    
    def format_context(self, docs: list[Document]) -> str:
        print(self.format_context_with_metadata(docs))
        return "\n\n".join(doc.page_content for doc in docs)
    
    def format_context_with_metadata(self, docs: list[Document]) -> str:
        formatted = []
        for doc in docs:
            content = doc.page_content
            meta = doc.metadata or {}
            meta_str = ", ".join(f"{k}: {v}" for k, v in meta.items())
            formatted.append(f"Context:\n{content}\n\nMetadata:\n{meta_str}")
        return "\n\n---\n\n".join(formatted)
    
    def generate_queries(self, query: str, k: int = 4):
        prompt = f"""
        Você é um especialista em busca de informações em editais acadêmicos.

        Gere {k} variações da pergunta abaixo para melhorar recuperação em um sistema RAG.

        Regras:
        - retorne no máximo 4 itens
        - nunca gere mais que 4
        - não explique nada
        - Não responda a pergunta
        - Use linguagem de editais (bolsa, PIBIC, seleção, edital, pesquisa, extensão)
        - Cada query deve ser diferente
        - Foque em intenções diferentes do usuário
        

        Pergunta:
        {query}

        Retorne uma lista com uma query por linha.
        """

        structured_llm = self.llm.with_structured_output(QueryList)
        response = structured_llm.invoke(prompt)

        return response.queries[:3] 
    

    def _multi_query_retrieve(self, query: str):
        queries = self.generate_queries(query)
        all_docs = []

        for q in queries:
           print(q)
           docs = self.retrieve(q)
           all_docs.extend(docs)

        
        return self.deduplicate(all_docs)
        

    def deduplicate(self, docs):
        print("desduplicando documentos")
        print("quantidade inicial de documentos encontrados:", len(docs))
        seen = set()
        unique_docs = []
        for doc in docs:
            key = doc.metadata.get("id") or doc.page_content[:200]

            if key not in seen:
                seen.add(key)
                unique_docs.append(doc)

        print("quantidade de documentos que restaram: ", len(unique_docs))
        return unique_docs

