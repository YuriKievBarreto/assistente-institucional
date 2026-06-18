from fastapi import APIRouter

chat_router = APIRouter()

@chat_router.get("/")
async def test():
    return "working"
