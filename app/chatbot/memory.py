from langchain_core.chat_history import InMemoryChatMessageHistory
from app.models.chat_model import ChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage

class MemoryManager:
    def __init__(
        self, 
        session_id: str, 
        window_size: int = 10, 
        history: list[ChatMessageHistory] | None = None
    ) -> None:
        self.session_id = session_id
        self.window_size = window_size
        self.history = InMemoryChatMessageHistory()
        if history:
            self.load_history(history)

    def load_history(self, history: list[ChatMessageHistory]) -> None:
        for message in history:
            if message.role == "human":
                self.history.add_message(HumanMessage(content=message.content))
            else:
                self.history.add_message(AIMessage(content=message.content))

    def get_history(self) -> list:
        # Retorna as últimas mensagens respeitando a janela de memória (window_size)
        return self.history.messages[-self.window_size:] if self.window_size else self.history.messages

    def get_store(self) -> InMemoryChatMessageHistory:
        return self.history

    def clear(self) -> None:
        self.history.clear()
