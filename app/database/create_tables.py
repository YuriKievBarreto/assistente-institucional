from sqlmodel import SQLModel
from app.database.postgres import engine
from app.models.all_models import Chat, Message, User, UserAccount

def create_tables():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)