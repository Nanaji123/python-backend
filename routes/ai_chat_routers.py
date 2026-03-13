from fastapi import APIRouter, Request, Response
from controllers.ai_controller import (
    gemini_chat_controller, create_ai_chat_controller, 
    get_ai_chats_controller, get_ai_chat_details_controller,
    delete_ai_chat_controller
)
from models.ai_chat_model import GeminiChatRequest

router = APIRouter(prefix="/ai")


@router.post("/ai-chat")
async def ai_chat(data: GeminiChatRequest, request: Request, response: Response):
    return await gemini_chat_controller(data, request)

@router.post("/create")
async def create_ai_chat(request: Request):
    return await create_ai_chat_controller(request)

@router.get("/chats")
async def get_ai_chats(request: Request):
    return await get_ai_chats_controller(request)

@router.get("/chat/{chat_id}")
async def get_ai_chat_details(chat_id: str, request: Request):
    return await get_ai_chat_details_controller(chat_id, request)

@router.post("/delete/{chat_id}")
async def delete_ai_chat(chat_id: str, request: Request):
    return await delete_ai_chat_controller(chat_id, request)

