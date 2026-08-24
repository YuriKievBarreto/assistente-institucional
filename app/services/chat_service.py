from app.chatbot.engine import ChatEngine
from app.models.chat_model import ChatInputRequest, ChatMigrateRequest, Chat, ChatCreate
from app.models.message_model import Message, MessageCreate
import uuid
from app.models.user_model import User
from typing import AsyncGenerator
from sqlmodel import Session
from app.repositories.interfaces.chat_repository_interface import IChatRepository
from app.repositories.interfaces.message_repository_interface import IMessageRepository



class ChatService:
    def __init__(
            self,
            chat_repo: IChatRepository,
            message_repo: IMessageRepository):

        self.chat_repo = chat_repo
        self.message_repo = message_repo

    async def chat(self, chat_engine: ChatEngine, req: ChatInputRequest):
        chat_engine.memory.load_history(req.history)
        answer = await chat_engine.stream_chat(req.query)
        return answer

    def migrate_chats(self, session: Session, migrate_data: ChatMigrateRequest, user_id: uuid.UUID) -> None:
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
        


    async def chat_and_save(self, engine: ChatEngine, req: ChatInputRequest, session: Session, current_user: User | None) -> AsyncGenerator[str, None]:
        engine.memory.load_history(req.history)
        full_response = ""

        async for chunk in engine.stream_chat(req.query):
            full_response += chunk
            yield chunk

        if current_user:
            self.save_dialogue(
                session=session,
                user_id=current_user.id,
                chat_id=req.session_id,
                title=req.title,
                human_message=req.query,
                ai_response=full_response
            )


    def save_dialogue(
    self,
    session: Session,
    user_id: uuid.UUID,
    chat_id: str,
    title: str,
    human_message: str,
    ai_response: str
    ) -> None:
        try:
            try:
                valid_chat_id = uuid.UUID(str(chat_id))
            except (ValueError, TypeError):
                valid_chat_id = None

            chat = self.chat_repo.find_chat_by_id(session, valid_chat_id) if valid_chat_id else None
            
            if not chat:
                new_chat = ChatCreate(title=title)
                chat = self.chat_repo.create_chat(session, new_chat, user_id)

            self.save_message(session, MessageCreate(role="human", content=human_message), chat.id)
            self.save_message(session, MessageCreate(role="ai", content=ai_response), chat.id)
        except Exception as e:
            session.rollback()
            import logging
            logging.getLogger(__name__).error(f"Erro ao salvar diálogo no banco: {e}")

    
    def save_message(self, session: Session, message_data: MessageCreate, chat_id: uuid.UUID) -> Message:
        return self.message_repo.create_message(session, message_data, chat_id)


    def find_chats_by_user_id(self, session: Session, user_id: uuid.UUID) -> list[Chat]:
        chats = self.chat_repo.find_chats_by_user_id(session, user_id)
        return chats







