from langchain_core.chat_history import InMemoryChatMessageHistory
from app.models.chat_model import ChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage

class MemoryManager:
    def __init__(self, session_id: str, window_size =10, history: list[ChatMessageHistory] = []) -> None:
        self.session_id = session_id
        self.history = InMemoryChatMessageHistory()
        self.load_history(history)

    
    def load_history(self, history: list[ChatMessageHistory]) -> None:
        for message in history:
            if message.role == "human":
                self.history.add_message(HumanMessage(content=message.content))
            else:
                self.history.add_message(AIMessage(content=message.content))

    def get_history(self) -> list:
        return self.history.messages

    def get_store(self) -> InMemoryChatMessageHistory:
        return self.history

    def clear(self) -> None:
        self.history.clear
