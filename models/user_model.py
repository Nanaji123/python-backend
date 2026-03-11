from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserChangePassword(BaseModel):
    current_password: str
    new_password: str


class User(BaseModel):

    username: str
    email: EmailStr
    password: str

    usernamechangeCount: int = 5
    lastUsernameChangeAt: Optional[datetime] = None

    profile_picture: str = "https://api.dicebear.com/7.x/avataaars/svg?seed=default"

    loginAttempts: int = 0
    lockUntil: Optional[datetime] = None

    isVerified: bool = False
    is2FAEnabled: bool = False
    isOnline: bool = False

    lastSeen: datetime = datetime.utcnow()

    createdAt: datetime = datetime.utcnow()
    updatedAt: datetime = datetime.utcnow()