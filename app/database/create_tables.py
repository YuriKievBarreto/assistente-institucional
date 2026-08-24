from sqlmodel import SQLModel
from app.database.postgres import engine
from app.models.tables import UserTable, ChatTable, MessageTable, UserAccountTable

def create_tables():
    SQLModel.metadata.create_all(engine)