from langchain_core.chat_history import BaseChatMessageHistory
from langchain_classic.memory import ConversationBufferWindowMemory
class MemoryManager:
    def __init__(self, session_id: str, window_size =10) -> None:
        self.session_id = session_id
        self.memory = ConversationBufferWindowMemory(
            k=window_size,
            return_messages=True,
            memory_key="chat_history"
        )

    def get_memory(self) -> ConversationBufferWindowMemory:
        return self.memory

    def clear(self) -> None:
        self.memory.clear()

    def get_history(self) -> list:
        return self.memory.chat_memory.messages
