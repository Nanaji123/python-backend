from fastapi import FastAPI
from routes.auth_routers import router as auth_router

app = FastAPI(
    title="Chat App Backend",
    version="1.0.0"
)

app.include_router(auth_router)

@app.get("/")
async def root():
    return {"message": "Backend running 🚀"}