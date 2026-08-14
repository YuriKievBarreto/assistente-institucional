from langchain_groq import ChatGroq
from app.chatbot.rag_logic import RAGRetriever
from app.chatbot.memory import MemoryManager
from app.chatbot.models import RAGConfig
from langchain_qdrant import QdrantVectorStore

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.runnables import  RunnableParallel, RunnableLambda
from app.chatbot.llm import get_bedrock_llm, get_groq_llm, get_google_llm
from langchain_core.language_models.chat_models import BaseChatModel
import os
from dotenv import load_dotenv




class ChatEngine:
    def __init__(
            self,
            memory_manager: MemoryManager,
            config: RAGConfig,
            retriever: RAGRetriever
    ):
        self.config = config
        self.memory = memory_manager
        self.llm = get_groq_llm(self.config)
        self.retriever = retriever
        
        
        
        self.chain = self.build_chain()

    
    def retrieve_and_format(self, x):
        docs = self.retriever._multi_query_retrieve(x["question"])
        return self.retriever.format_context_with_metadata(docs)

    def build_chain(self):
        prompt = ChatPromptTemplate.from_messages([
        ("system",  """
                Você é o assistente institucional do IFPB — Campus Cajazeiras.
                Sua personalidade é prestativa e bem-humorada, mas isso se reflete no TOM da resposta, não no tamanho dela.

                FORMATO:
                - Responda com HTML puro: <p>, <strong>, <ul>, <li>, <br>
                - Nunca use markdown

                RESPOSTA:
                - Responda apenas o que foi perguntado, sem adicionar explicações, contexto adicional ou 
                interpretações não solicitadas
                - Para perguntas objetivas (status, data, número, valor, nome), a resposta deve conter APENAS 
                o fato pedido — nada além disso
                - Não adicione frases como "isso significa que..." ou "em outras palavras..." a menos que o 
                usuário peça explicitamente uma explicação
                - Use listas apenas quando houver múltiplos itens a enumerar

                CONTEÚDO:
                - Priorize o contexto fornecido para responder
                - Utilize apenas as partes do contexto que forem diretamente relevantes para a pergunta
                - Ignore informações irrelevantes no contexto, mesmo que estejam no mesmo documento
                - Se não encontrar a informação específica solicitada no contexto, diga isso claramente e pare
                - NÃO inclua informações sobre tópicos relacionados mas diferentes do que foi perguntado 
                (ex: se perguntarem sobre a disciplina X e o contexto só tiver a disciplina Y, não liste a Y — 
                apenas informe que não encontrou informação sobre X)
                - Só forneça informação parcial se ela responder diretamente a uma PARTE da pergunta original, 
                nunca como substituto de uma informação que não foi encontrada

                Ao final da resposta, inclua a fonte e URL presentes no contexto. utilize tag <a> para URLs
                Contexto:
                {context}

                
                """),
                    MessagesPlaceholder("chat_history"),
                    ("human", "{question}")
                ])

    
        #
        chain = (
        RunnableParallel(
            question=lambda x: x["question"],
            context=RunnableLambda(self.retrieve_and_format),
            chat_history=lambda x: self.memory.get_history()
        )
        | prompt
        | self.llm
    )

        return chain
        
    def chat(self, question: str):
        response = self.chain.invoke({"question": question})
        content = str(response.content)

        return content

    async def stream_chat(self, question: str):
        async for chunk in self.chain.astream({"question": question}):
            text = chunk.content
            if text:
                yield text

        
        
        
        