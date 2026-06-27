from app.chatbot.engine import ChatEngine
from app.models.chat_model import ChatInputRequest, ChatMigrateRequest, Chat, ChatCreate, Dialogue, AIresponse
from app.models.message_model import Message, MessageCreate
import uuid
from sqlmodel import Session
from app.repositories import chat_repository, message_repository

def chat(chat_engine: ChatEngine, req: ChatInputRequest):
    chat_engine.memory.load_history(req.history)
    answer = chat_engine.chat(req.query)
    return AIresponse(answer=answer)


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


def save_dialogue(session: Session, dialogue_data: Dialogue):
    print("iniciando salvamento de dialogo")
    chat = chat_repository.find_chat_by_id(session, uuid.UUID(dialogue_data.chat_id))
    print("há chat? ", chat)
    
    if not chat:
        print("chat nao encontrado no banco de dados. criando....")
        new_chat = ChatCreate(title=dialogue_data.title)
        chat = chat_repository.create_chat(session, new_chat, dialogue_data.user_id)
        print("chat criado com sucesso! ",chat)


    print("print salvando mesanges")
    save_message(session, MessageCreate(role="human", content=dialogue_data.human_message), chat.id)
    save_message(session, MessageCreate(role="ai", content=dialogue_data.AI_response), chat.id)


def save_message(session: Session, message_data: MessageCreate, chat_id):
    return message_repository.create_message(session, message_data, chat_id)


