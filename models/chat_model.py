from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    message: str

class ChatRequest(BaseModel):
    message: str
    chat_id: str

