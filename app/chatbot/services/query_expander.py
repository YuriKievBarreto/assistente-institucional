from langchain_core.language_models.chat_models import BaseChatModel
from app.chatbot.models import QueryList
import logging

logger = logging.getLogger(__name__)

class QueryExpander:
    """
        Serviço responsável por expandir uma pergunta do usuário em múltiplas 
        variações focadas em linguagem de editais institucionais via LLM.
    """
    def __init__(self, llm: BaseChatModel):
        self.llm = llm.with_structured_output(QueryList, method="json_mode")

    def expand(self, query: str, k: int = 3) -> list[str]:
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

        try:
            response = self.llm.invoke(prompt)
            generated_queries = response.queries[:k]
            # Retorna a pergunta original seguida das variações
            return [query] + generated_queries
        except Exception as e:
            logger.warning(f"Falha ao gerar variações da query via LLM: {e}. Mantendo apenas a query original.")
            return [query]  # Fallback gracioso caso o LLM falhe
