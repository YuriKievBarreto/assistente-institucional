from langchain_groq import ChatGroq
from app.chatbot.rag_logic import RAGRetriever
from app.chatbot.memory import MemoryManager

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableParallel

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
        prompt  = ChatPromptTemplate.from_messages(
            [("system", 
                """
                    Você é o assistente institucional do IFPB - Campus Cajazeiras. Sua personalidade é bem-humorada e prestativa, e você é um especialista rigoroso nas normas do IFPB.

                    SUAS DIRETRIZES DE FORMATO:
                    1. Você DEVE responder utilizando tags HTML para estruturar a informação.
                    2. Utilize <strong> para dar ênfase em conceitos ou nomes de documentos.
                    3. Utilize <ul> e <li> para listar itens, requisitos ou obrigações.
                    4. Utilize <p> para separar parágrafos e <br> para quebras de linha simples quando necessário.
                    5. NÃO utilize markdown como asteriscos (*) ou hashtags (#), apenas HTML puro.

                    DIRETRIZES DE CONTEÚDO:
                    1. Responda estritamente com base no contexto.
                    2. Se a informação não estiver no contexto, diga claramente que não a encontrou.
                    3. Sempre cite a fonte (ex: <strong>Resolução 30/2026</strong>) e a url de referência para dar autoridade.

                    Contexto fornecido:
                    {context}


                """
             
             ),

                MessagesPlaceholder("chat_history"),
                ("human", "{question}")]
        )

        return RunnableParallel(
            question=RunnablePassthrough(),
            context = lambda x: self.retriever.format_context(
                self.retriever.retrieve(x["question"])
            ),
            chat_history = lambda x: self.memory.get_history()
        ) | prompt | self.llm
    
    def chat(self, question: str):
        response = self.chain.invoke({"question": question})
        content = str(response.content)
        self.memory.get_memory().save_context(
            {"input": question},
            {"output": content}
        )

        return response.content

        
        
        
        