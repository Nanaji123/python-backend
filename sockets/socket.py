import socketio
from jose import jwt
from bson import ObjectId
from utils.database import db
import os
from datetime import datetime


SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"


sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*"
)

print("Socket server initialized")


# =========================
# CONNECT + AUTH
# =========================

@sio.event
async def connect(sid, environ, auth):

    try:

        cookies = environ.get("HTTP_COOKIE")

        token = None

        if cookies:
            for cookie in cookies.split(";"):
                cookie = cookie.strip()
                if cookie.startswith("access_token="):
                    token = cookie.split("=")[1]

        if not token:
            raise Exception("No token provided")

        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        user = await db.users.find_one({
            "_id": ObjectId(decoded["id"])
        })

        if not user:
            raise Exception("User not found")

        await sio.save_session(sid, {"user": user})

        print("User connected:", user["_id"])

        # join personal room
        await sio.enter_room(sid, str(user["_id"]))

    except Exception as e:
        print("Socket auth error:", e)
        return False


# =========================
# JOIN CHAT
# =========================

@sio.event
async def join_chat(sid, chat_id):

    await sio.enter_room(sid, chat_id)

    print("User joined chat:", chat_id)


# =========================
# SEND MESSAGE
# =========================

@sio.event
async def send_message(sid, data):

    try:

        session = await sio.get_session(sid)
        user = session["user"]

        chat_id = data["chatId"]
        content = data["content"]

        now = datetime.utcnow()
        message = {
            "chat": chat_id, # Keep as string for emission
            "sender": str(user["_id"]),
            "content": content,
            "createdAt": now.isoformat(),
            "updatedAt": now.isoformat()
        }

        # For database insertion
        db_message = {
            "chat": ObjectId(chat_id),
            "sender": user["_id"],
            "content": content,
            "createdAt": now,
            "updatedAt": now
        }
        result = await db.messages.insert_one(db_message)

        message["_id"] = str(result.inserted_id)

        message["sender"] = {
            "_id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"],
            "profile_picture": user.get("profile_picture")
        }

        # update latest message
        await db.chats.update_one(
            {"_id": ObjectId(chat_id)},
            {"$set": {
                "latestMessage": result.inserted_id,
                "updatedAt": datetime.utcnow()
            }}
        )

        # send message to sender
        await sio.emit(
            "receive_message",
            {**message, "isMine": True},
            room=sid
        )

        # send to chat room
        await sio.emit(
            "receive_message",
            {**message, "isMine": False},
            room=chat_id,
            skip_sid=sid
        )

        # notifications
        chat = await db.chats.find_one({"_id": ObjectId(chat_id)})

        for user_id in chat["users"]:
            if str(user_id) != str(user["_id"]):

                await sio.emit(
                    "message_notification",
                    {
                        **message,
                        "chatId": chat_id # Ensure chatId is present and string
                    },
                    room=str(user_id)
                )

    except Exception as e:
        print("Socket send_message error:", e)


# =========================
# TYPING EVENT
# =========================

@sio.event
async def typing(sid, chat_id):

    session = await sio.get_session(sid)
    user = session["user"]

    await sio.emit(
        "typing",
        {
            "userId": str(user["_id"]),
            "username": user["username"]
        },
        room=chat_id,
        skip_sid=sid
    )


# =========================
# STOP TYPING
# =========================

@sio.event
async def stop_typing(sid, chat_id):

    session = await sio.get_session(sid)
    user = session["user"]

    await sio.emit(
        "stop_typing",
        str(user["_id"]),
        room=chat_id,
        skip_sid=sid
    )


# =========================
# DISCONNECT
# =========================

@sio.event
async def disconnect(sid):

    try:

        session = await sio.get_session(sid)
        user = session.get("user")

        print("User disconnected:", user["_id"])

    except:
        print("Socket disconnected")