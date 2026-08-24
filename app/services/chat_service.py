from app.chatbot.engine import ChatEngine
from app.models.chat_model import ChatInputRequest, ChatMigrateRequest, Chat, ChatCreate, ChatResponse
from app.models.message_model import Message, MessageCreate, MessageResponse
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

    def migrate_chats(self, migrate_data: ChatMigrateRequest, user_id: uuid.UUID) -> None:
        try:
            for chat_data in migrate_data.chats_data:
                new_chat = ChatCreate(title=chat_data.title)
                chat = self.chat_repo.create_chat(new_chat, user_id)

                for msg in chat_data.history:
                    message_data = MessageCreate(role=msg.role, content=msg.content)
                    self.message_repo.create_message(message_data, chat.id)
        except Exception as e:
            self.chat_repo.rollback()
            import logging
            logging.getLogger(__name__).error(f"Erro ao migrar chats no banco: {e}")
            raise

    async def chat_and_save(self, engine: ChatEngine, req: ChatInputRequest, current_user: User | None) -> AsyncGenerator[str, None]:
        engine.memory.load_history(req.history)
        full_response = ""

        async for chunk in engine.stream_chat(req.query):
            full_response += chunk
            yield chunk

        if current_user:
            self.save_dialogue(
                user_id=current_user.id,
                chat_id=req.session_id,
                title=req.title,
                human_message=req.query,
                ai_response=full_response
            )


    def save_dialogue(
        self,
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

            chat = self.chat_repo.find_chat_by_id(valid_chat_id) if valid_chat_id else None
            
            if not chat:
                new_chat = ChatCreate(title=title)
                chat = self.chat_repo.create_chat(new_chat, user_id)

            self.save_message(MessageCreate(role="human", content=human_message), chat.id)
            self.save_message(MessageCreate(role="ai", content=ai_response), chat.id)
        except Exception as e:
            self.chat_repo.rollback()
            import logging
            logging.getLogger(__name__).error(f"Erro ao salvar diálogo no banco: {e}")



    
    def save_message(self, message_data: MessageCreate, chat_id: uuid.UUID) -> Message:
        return self.message_repo.create_message(message_data, chat_id)


    def find_chats_by_user_id(self, user_id: uuid.UUID) -> list[ChatResponse]:
        chats = self.chat_repo.find_chats_by_user_id(user_id)
        return [
            ChatResponse(
                id=chat.id,
                title=chat.title,
                created_at=chat.created_at,
                messages=[
                    MessageResponse(
                        id=msg.id,
                        role=msg.role,
                        content=msg.content,
                        created_at=msg.created_at
                    )
                    for msg in chat.messages
                ]
            )
            for chat in chats
        ]
