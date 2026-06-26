from app.chatbot.engine import ChatEngine
from app.models.chat_model import MessageHistory, ChatInputRequest


def chat(chat_engine: ChatEngine, req: ChatInputRequest):
    chat_engine.memory.load_history(req.history)
    answer = chat_engine.chat(req.query)
    return {"answer": answer}