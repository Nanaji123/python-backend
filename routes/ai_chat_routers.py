from fastapi import APIRouter, Request, Response
from controllers.ai_controller import (
    gemini_chat_controller, create_ai_chat_controller, 
    get_ai_chats_controller, get_ai_chat_details_controller,
    delete_ai_chat_controller
)
from models.ai_chat_model import GeminiChatRequest
from fastapi import Depends
from utils.auth_deps import get_current_user

router = APIRouter(prefix="/ai")


@router.post("/ai-chat")
async def ai_chat(data: GeminiChatRequest, user_id: str = Depends(get_current_user)):
    return await gemini_chat_controller(data, user_id)

@router.post("/create")
async def create_ai_chat(user_id: str = Depends(get_current_user)):
    return await create_ai_chat_controller(user_id)

@router.get("/chats")
async def get_ai_chats(user_id: str = Depends(get_current_user)):
    return await get_ai_chats_controller(user_id)

@router.get("/chat/{chat_id}")
async def get_ai_chat_details(chat_id: str, user_id: str = Depends(get_current_user)):
    return await get_ai_chat_details_controller(chat_id, user_id)

@router.post("/delete/{chat_id}")
async def delete_ai_chat(chat_id: str, user_id: str = Depends(get_current_user)):
    return await delete_ai_chat_controller(chat_id, user_id)

