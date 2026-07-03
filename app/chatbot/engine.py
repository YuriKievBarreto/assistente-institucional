from langchain_groq import ChatGroq
from app.chatbot.rag_logic import RAGRetriever
from app.chatbot.memory import MemoryManager

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel, RunnableLambda

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
        self.llm = ChatGroq(model="llama-3.1-8b-instant", api_key=os.getenv("GROQ_API_KEY"), temperature=0.1)
        self.chain = self.build_chain()

    def build_chain(self):
        prompt = ChatPromptTemplate.from_messages([
        ("system", """
            Você é o assistente institucional do IFPB — Campus Cajazeiras.
            Sua personalidade é prestativa e bem-humorada.

            FORMATO:
            - Responda com HTML puro: <p>, <strong>, <ul>, <li>, <br>
            - Nunca use markdown

            RESPOSTA:
            - Seja direto: responda a pergunta em no máximo 2 frases antes de qualquer detalhe adicional
            - Use listas apenas quando houver múltiplos itens a enumerar
            - Não adicione parágrafos de aviso ou sugestões não solicitadas

            CONTEÚDO:
            - Responda apenas com base no contexto fornecido
            - Se não encontrar a informação, diga apenas: "Não encontrei essa informação nos documentos disponíveis."
            - Cite a fonte e URL ao final, após a resposta principal

            Contexto:
            {context}
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

        
        
        
        