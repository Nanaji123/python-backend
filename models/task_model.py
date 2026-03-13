from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TaskCreate(BaseModel):
    title: str
    description: str
    due_date: str
    priority: str
    category: str

class TaskUpdate(BaseModel):
    id: str
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None

class TaskResponse(BaseModel):
    id: str
    title: str
    description: str
    due_date: str
    priority: str
    category: str
    status: str
    userId: str
    createdAt: datetime
    updatedAt: datetime
