from sqlmodel import create_engine, Session
import os
from dotenv import load_dotenv

load_dotenv()

PG_DATABASE_URL: str  = os.getenv("PG_DATABASE_URL")
engine = create_engine(PG_DATABASE_URL)

def get_session():
    with Session(engine) as session:
        yield session