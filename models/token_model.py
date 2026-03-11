from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class Token(BaseModel):

    userId: str
    token: str
    type: str
    expiresAt: datetime

    createdAt: Optional[datetime] = datetime.utcnow()
    updatedAt: Optional[datetime] = datetime.utcnow()