from pydantic import BaseModel
from typing import Optional

class GeminiChatRequest(BaseModel):
    message: str
    chatId: str
    persona: Optional[str] = None