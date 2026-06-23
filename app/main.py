from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database.create_tables import create_tables
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield

app = FastAPI(
    title="Assistente institucional - IFPB Campus Cajazeiras",
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")




