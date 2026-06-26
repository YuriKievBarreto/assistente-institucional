from app.chatbot.engine import ChatEngine
from app.models.chat_model import ChatInputRequest, ChatMigrateRequest, Chat
from app.models.message_model import Message
import uuid
from sqlmodel import Session

def chat(chat_engine: ChatEngine, req: ChatInputRequest):
    chat_engine.memory.load_history(req.history)
    answer = chat_engine.chat(req.query)
    return {"answer": answer}


def migrate_chats(session: Session, migrate_data: ChatMigrateRequest, user_id: uuid.UUID):
    messages_to_insert = []

    for chat_data in migrate_data.chats_data:
        chat = Chat(title=chat_data.title, user_id=user_id)
        session.add(chat)
        session.flush()

        for msg in chat_data.history:
            messages_to_insert.append(Message(
                chat_id=chat.id,
                role=msg.role,
                content=msg.content
            ))

    session.add_all(messages_to_insert)
    session.commit()
