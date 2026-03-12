from fastapi import APIRouter, Request, Response
from controllers.ai_controller import gemini_chat_controller
from models.ai_chat_model import GeminiChatRequest

router = APIRouter(prefix="/ai")


@router.post("/ai-chat")
async def ai_chat(data: GeminiChatRequest, request: Request, response: Response):
    return await gemini_chat_controller(data)
