from fastapi import HTTPException
from config.gemini import generate_gemini_response
from utils.database import db
from bson import ObjectId
from datetime import datetime

async def create_ai_chat_controller(user_id: str):
    new_chat = {
        "userId": user_id,
        "title": "New AI Chat",
        "messages": [],
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }
    result = await db.ai_chats.insert_one(new_chat)
    return {
        "success": True,
        "chatId": str(result.inserted_id)
    }

async def get_ai_chats_controller(user_id: str):
    chats = []
    cursor = db.ai_chats.find({"userId": user_id}).sort("updatedAt", -1)
    async for chat in cursor:
        chats.append({
            "id": str(chat["_id"]),
            "title": chat.get("title", "AI Chat"),
            "updatedAt": chat["updatedAt"]
        })
    return {
        "success": True,
        "chats": chats
    }

async def get_ai_chat_details_controller(chat_id: str, user_id: str):
    if not ObjectId.is_valid(chat_id):
        raise HTTPException(status_code=400, detail="Invalid chat ID")
    
    chat = await db.ai_chats.find_one({"_id": ObjectId(chat_id), "userId": user_id})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    return {
        "success": True,
        "chat": {
            "id": str(chat["_id"]),
            "title": chat.get("title", "AI Chat"),
            "messages": chat.get("messages", []),
            "persona": chat.get("persona")
        }
    }

async def gemini_chat_controller(data, user_id: str):
    message_text = data.message
    chat_id = data.chatId
    persona = data.persona

    if not message_text:
        raise HTTPException(status_code=400, detail="Message is required")
    if not chat_id or not ObjectId.is_valid(chat_id):
        raise HTTPException(status_code=400, detail="Valid Chat ID is required")

    try:
        # Check if chat already has a persona
        chat = await db.ai_chats.find_one({"_id": ObjectId(chat_id)})
        current_persona = chat.get("persona") if chat else None
        
        # Use provided persona for new chats, or existing one for others
        active_persona = persona or current_persona

        ai_reply = await generate_gemini_response(message_text, active_persona)

        # Update chat history
        user_msg = {
            "id": str(ObjectId()),
            "text": message_text,
            "sender": "user",
            "timestamp": datetime.utcnow()
        }
        ai_msg = {
            "id": str(ObjectId()),
            "text": ai_reply,
            "sender": "ai",
            "timestamp": datetime.utcnow()
        }

        # Update title if it's the first message
        chat = await db.ai_chats.find_one({"_id": ObjectId(chat_id)})
        update_query = {
            "$push": {"messages": {"$each": [user_msg, ai_msg]}},
            "$set": {"updatedAt": datetime.utcnow()}
        }
        if chat and (not chat.get("messages") or len(chat["messages"]) == 0):
            update_query["$set"]["title"] = message_text[:30] + ("..." if len(message_text) > 30 else "")
            if persona:
                update_query["$set"]["persona"] = persona

        await db.ai_chats.update_one(
            {"_id": ObjectId(chat_id), "userId": user_id},
            update_query
        )

        return {
            "success": True,
            "reply": ai_reply
        }

    except Exception as e:
        print("Gemini AI Error:", e)
        raise HTTPException(status_code=500, detail="AI response failed")


async def delete_ai_chat_controller(chat_id: str, user_id: str):
    if not ObjectId.is_valid(chat_id):
        raise HTTPException(status_code=400, detail="Invalid chat ID")
    
    result = await db.ai_chats.delete_one({"_id": ObjectId(chat_id), "userId": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    return {
        "success": True,
        "message": "Chat deleted successfully"
    }
