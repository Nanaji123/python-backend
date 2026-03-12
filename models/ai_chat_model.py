from pydantic import BaseModel


class GeminiChatRequest(BaseModel):
    message: str