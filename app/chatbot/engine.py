from langchain_groq import ChatGroq
from app.chatbot.rag_logic import RAGRetriever
from app.chatbot.memory import MemoryManager

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel, RunnableLambda
from app.chatbot.llm import get_bedrock_llm, get_groq_llm
import os
from dotenv import load_dotenv




class ChatEngine:
    def __init__(
            self,
            rag_retriever: RAGRetriever,
            memory_manager: MemoryManager
    ):
        self.retriever = rag_retriever
        self.memory = memory_manager
        self.llm = get_bedrock_llm(self.retriever.config)
        self.chain = self.build_chain()

    def build_chain(self):
        prompt = ChatPromptTemplate.from_messages([
        ("system",  """
                Você é o assistente institucional do IFPB — Campus Cajazeiras.
                Sua personalidade é prestativa e bem-humorada.

                FORMATO:
                - Responda com HTML puro: <p>, <strong>, <ul>, <li>, <br>
                - Nunca use markdown

                RESPOSTA:
                - Seja direto e objetivo
                - Use listas apenas quando houver múltiplos itens a enumerar

                CONTEÚDO:
                - Priorize o contexto fornecido para responder
                - Utilize apenas as partes do contexto que forem diretamente relevantes para a pergunta
                - Ignore informações irrelevantes no contexto
                - Se o contexto não for suficiente para uma resposta completa, responda apenas com o que for possível inferir dele
                - Se o contexto tiver informação parcial, responda com o que for possível. 
                Só recuse se o contexto for completamente irrelevante para a pergunta."

                Contexto:
                {context}

                Ao final da resposta, inclua a fonte e URL presentes no contexto.
                """),
                    MessagesPlaceholder("chat_history"),
                    ("human", "{question}")
                ])

        def retrieve_and_format(x):
            docs = self.retriever.retrieve(x["question"])
            return self.retriever.format_context_with_metadata(docs)

        chain = (
        RunnableParallel(
            question=lambda x: x["question"],
            context=RunnableLambda(retrieve_and_format),
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

        
        
        
        