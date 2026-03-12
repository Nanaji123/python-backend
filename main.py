from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.auth_routers import router as auth_router
from routes.ai_chat_routers import router as ai_chat_router
from routes.chat_routers import router as chat_router
import socketio
from sockets.socket import sio

app = FastAPI(
    title="Chat App Backend",
    version="1.0.0"
)

# CORS configuration
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],   # or ["GET","POST","DELETE","OPTIONS"]
    allow_headers=["*"],   # or ["Content-Type","Authorization"]
)

# Socket.IO
socket_app = socketio.ASGIApp(
    sio,
    other_asgi_app=app
)

# Routers
app.include_router(auth_router)
app.include_router(ai_chat_router)
app.include_router(chat_router)

@app.get("/")
async def root():
    return {"message": "Backend running 🚀"}