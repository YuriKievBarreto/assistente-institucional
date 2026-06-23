from fastapi import APIRouter

user_router = APIRouter()

@user_router.get("/")
async def test():
    return "working"