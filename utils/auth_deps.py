from fastapi import HTTPException, Request
from jose import jwt, JWTError
import os

SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"

async def get_current_user(request: Request):
    access_token = request.cookies.get("access_token")
    if not access_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            access_token = auth_header.split(" ")[1]
    if not access_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        decoded_token = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = decoded_token.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: user ID missing")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
