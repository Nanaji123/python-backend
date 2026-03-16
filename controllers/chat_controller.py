from fastapi import Request, UploadFile, File, Form, HTTPException
from bson import ObjectId
import json
import os
from datetime import datetime
import cloudinary.uploader
from utils.database import db
from math import ceil


async def populate_chat_data(chat):
    if not chat:
        return None

    # stringify id
    chat["_id"] = str(chat["_id"])

    # populate users
    users = []
    for user_id in chat.get("users", []):
        user = await db.users.find_one({"_id": user_id})
        if user:
            user["_id"] = str(user["_id"])
            user.pop("password", None)
            users.append(user)
    chat["users"] = users

    # populate group admin
    if chat.get("groupAdmin"):
        admin = await db.users.find_one({"_id": chat["groupAdmin"]})
        if admin:
            admin["_id"] = str(admin["_id"])
            admin.pop("password", None)
            chat["groupAdmin"] = admin
        else:
            chat["groupAdmin"] = None
    else:
        chat["groupAdmin"] = None

    # populate latest message
    latest_message = None
    if chat.get("latestMessage"):
        message = await db.messages.find_one({"_id": chat["latestMessage"]})
        if message:
            sender = await db.users.find_one({"_id": message.get("sender")})
            sender_data = None
            if sender:
                sender_data = {
                    "_id": str(sender["_id"]),
                    "username": sender.get("username"),
                    "email": sender.get("email"),
                    "profile_picture": sender.get("profile_picture")
                }

            latest_message = {
                "_id": str(message["_id"]),
                "content": message.get("content"),
                "sender": sender_data,
                "createdAt": message.get("createdAt"),
                "updatedAt": message.get("updatedAt"),
                "chat": str(message.get("chat"))
            }
    chat["latestMessage"] = latest_message
    
    return chat


async def list_user_controller(user_id: str, page: int = 1, limit: int = 20, search: str = ""):
    try:
        skip = (page - 1) * limit
        skip = (page - 1) * limit

        keyword = {}

        if search:
            keyword = {
                "$or": [
                    {"username": {"$regex": search, "$options": "i"}},
                    {"email": {"$regex": search, "$options": "i"}}
                ]
            }
        query = {
            **keyword,
            "_id": {"$ne": ObjectId(user_id)}
        }
        cursor = db.users.find(
            query,
            {
                "username": 1,
                "email": 1,
                "profile_picture": 1,
                "isOnline": 1,
                "lastSeen": 1
            }
        ).sort("createdAt", -1).skip(skip).limit(limit)

        users_list = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            users_list.append(doc)

        total = await db.users.count_documents(query)
        return {
            "success": True,
            "users": users_list,
            "total": total,
            "page": page,
            "pages": ceil(total / limit)
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        print("Error fetching users:", e)
        raise HTTPException(status_code=500, detail="Internal server error")

async def get_chats_controller(logged_user_id: str):

    try:

        # 1️⃣ Fetch chats where user is participant
        chats_cursor = db.chats.find({
            "users": ObjectId(logged_user_id)
        }).sort("updatedAt", -1)

        formatted_chats = []

        async for chat in chats_cursor:
            # Populate chat data using helper
            chat = await populate_chat_data(chat)
            users = chat["users"]
            latest_message = chat["latestMessage"]

            # 2️⃣ Private chat formatting
            if not chat.get("isGroupChat"):
                other_user = None
                for u in users:
                    if u["_id"] != logged_user_id:
                        other_user = u
                        break

                formatted_chats.append({
                    "_id": chat["_id"],
                    "chatName": other_user.get("username") if other_user else chat.get("chatName"),
                    "isGroupChat": False,
                    "otherUser": {
                        "_id": other_user.get("_id") if other_user else None,
                        "username": other_user.get("username") if other_user else None,
                        "email": other_user.get("email") if other_user else None,
                        "profile_picture": other_user.get("profile_picture") if other_user else None,
                        "isOnline": other_user.get("isOnline") if other_user else False,
                        "lastSeen": other_user.get("lastSeen") if other_user else None
                    },
                    "latestMessage": latest_message,
                    "createdAt": chat.get("createdAt"),
                    "updatedAt": chat.get("updatedAt")
                })

            else:
                # 3️⃣ Group chat formatting
                formatted_chats.append({
                    "_id": chat["_id"],
                    "chatName": chat.get("chatName"),
                    "isGroupChat": True,
                    "users": users,
                    "groupAdmin": chat.get("groupAdmin"),
                    "latestMessage": latest_message,
                    "createdAt": chat.get("createdAt"),
                    "updatedAt": chat.get("updatedAt"),
                    "chat_profile_picture": chat.get("chat_profile_picture"),
                    "groupDescription": chat.get("groupDescription", "")
                })

        return {
            "success": True,
            "count": len(formatted_chats),
            "chats": formatted_chats
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        print("Error fetching chats:", e)
        raise HTTPException(status_code=500, detail="Internal server error")

async def create_chat_controller(request: Request, logged_user_id: str):
    try:

        data = await request.json()
        user_id = data.get("userId") or data.get("user_id")

        if not user_id:
            raise HTTPException(status_code=400, detail="User ID is required")

        # 0️⃣ Check if target user exists
        target_user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")

        # 1️⃣ Check if chat already exists
        existing_chat = await db.chats.find_one({
            "users": {
                "$all": [ObjectId(logged_user_id), ObjectId(user_id)]
            },
            "isGroupChat": False
        })

        if existing_chat:
            # fetch and populate existing chat
            full_chat = await populate_chat_data(existing_chat)
            return {
                "success": True,
                "chat": full_chat
            }

        # 2️⃣ Create new chat
        new_chat_doc = {
            "users": [ObjectId(logged_user_id), ObjectId(user_id)],
            "isGroupChat": False,
            "chatName": target_user["username"],
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
        result = await db.chats.insert_one(new_chat_doc)

        # 3️⃣ Fetch and populate full chat
        full_chat = await db.chats.find_one({"_id": result.inserted_id})
        full_chat = await populate_chat_data(full_chat)

        return {
            "success": True,
            "chat": full_chat
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        print("Error creating chat:", e)
        raise HTTPException(status_code=500, detail="Internal server error")

async def update_chat_controller(request: Request, logged_user_id: str):
    try:

        data = await request.json()
        chat_id = data.get("chat_id")
        chat_name = data.get("chat_name")
        chat_profile_picture = data.get("chat_profile_picture")
        group_description = data.get("group_description")

        if not chat_id:
            raise HTTPException(status_code=400, detail="Chat ID is required")

        # 1️⃣ Update chat
        updated_chat = await db.chats.update_one(
            {"_id": ObjectId(chat_id)},
            {
                "$set": {
                    "chatName": chat_name,
                    "chat_profile_picture": chat_profile_picture,
                    "groupDescription": group_description,
                    "updatedAt": datetime.utcnow()
                }
            }
        )

        if updated_chat.modified_count == 0:
             raise HTTPException(status_code=404, detail="Chat not found or no changes made")

        full_chat = await db.chats.find_one({"_id": ObjectId(chat_id)})
        full_chat = await populate_chat_data(full_chat)

        return {
            "success": True,
            "chat": full_chat
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        print("Error updating chat:", e)
        raise HTTPException(status_code=500, detail="Internal server error")

async def delete_chat_controller(request: Request, user_id: str):
    try:

        data = await request.json()
        chat_id = data.get("chat_id")

        if not chat_id:
            raise HTTPException(status_code=400, detail="Chat ID is required")

        # 1️⃣ Fetch chat before deleting
        chat_to_delete = await db.chats.find_one({"_id": ObjectId(chat_id)})
        if not chat_to_delete:
            raise HTTPException(status_code=404, detail="Chat not found")

        # 2️⃣ Delete chat
        await db.chats.delete_one({"_id": ObjectId(chat_id)})

        return {
            "success": True,
            "chat": {
                "_id": str(chat_id),
                "chatName": chat_to_delete.get("chatName"),
                "isGroupChat": chat_to_delete.get("isGroupChat")
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        print("Error deleting chat:", e)
        raise HTTPException(status_code=500, detail="Internal server error")

async def get_messages_controller(chat_id: str, logged_user_id: str, page: int = 1, limit: int = 30):
    try:
        skip = (page - 1) * limit

        # 2️⃣ Fetch messages
        cursor = db.messages.find({
            "chat": ObjectId(chat_id)
        }).sort("createdAt", -1).skip(skip).limit(limit)

        messages = []

        async for msg in cursor:
            msg["_id"] = str(msg["_id"])
            msg["chat"] = str(msg["chat"])

            # 3️⃣ Fetch and populate sender
            sender = await db.users.find_one({"_id": msg["sender"]})

            if sender:
                sender["_id"] = str(sender["_id"])
                sender_data = {
                    "_id": sender["_id"],
                    "username": sender.get("username"),
                    "email": sender.get("email"),
                    "profile_picture": sender.get("profile_picture")
                }
            else:
                sender_data = None

            messages.append({
                "_id": msg["_id"],
                "content": msg["content"],
                "chat": msg["chat"],
                "sender": sender_data,
                "readBy": msg.get("readBy", []),
                "createdAt": msg.get("createdAt"),
                "updatedAt": msg.get("updatedAt"),
                "isMine": str(sender_data["_id"]) == logged_user_id if sender_data else False
            })

        return {
            "success": True,
            "messages": messages
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        print("Error fetching messages:", e)
        raise HTTPException(status_code=500, detail="Internal server error")

async def create_group_chat_controller(
    logged_user_id: str,
    users: str = Form(...),
    groupName: str = Form(...),
    groupDescription: str = Form(""),
    image: UploadFile = File(None)
):

    try:

        # 2️⃣ Parse users
        users_list = json.loads(users)

        if not users_list or not groupName:
            raise HTTPException(
                status_code=400,
                detail="Users and group name are required"
            )

        if not isinstance(users_list, list) or len(users_list) < 2:
            raise HTTPException(
                status_code=400,
                detail="Group chat requires at least 3 members"
            )

        chat_profile_picture = ""

        # 3️⃣ Upload image to Cloudinary
        if image:

            result = cloudinary.uploader.upload(
                image.file,
                folder="chat_profile_pictures"
            )

            chat_profile_picture = result["secure_url"]

        # 4️⃣ Normalize user list
        unique_users = list(set([str(u) for u in users_list]))

        if logged_user_id not in unique_users:
            unique_users.append(logged_user_id)

        users_object_ids = [ObjectId(u) for u in unique_users]

        # 5️⃣ Create group chat
        chat_data = {
            "chatName": groupName,
            "users": users_object_ids,
            "isGroupChat": True,
            "groupAdmin": ObjectId(logged_user_id),
            "chat_profile_picture": chat_profile_picture,
            "groupDescription": groupDescription or "",
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }

        result = await db.chats.insert_one(chat_data)

        # 6️⃣ Fetch and populate chat
        full_chat = await db.chats.find_one({"_id": result.inserted_id})
        full_chat = await populate_chat_data(full_chat)

        return {
            "success": True,
            "chat": full_chat
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        print("Error creating group chat:", e)
        raise HTTPException(status_code=500, detail="Internal server error")

async def get_chat_details_controller(chat_id: str, logged_user_id: str):
    try:

        # 2️⃣ Fetch chat
        chat = await db.chats.find_one({"_id": ObjectId(chat_id)})

        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        # 3️⃣ Populate chat
        chat = await populate_chat_data(chat)
        users = chat["users"]

        # 4️⃣ Base response
        response_data = {
            "_id": chat["_id"],
            "isGroupChat": chat["isGroupChat"],
            "chatName": chat.get("chatName"),
            "chat_profile_picture": chat.get("chat_profile_picture"),
            "createdAt": chat.get("createdAt"),
            "updatedAt": chat.get("updatedAt"),
            "groupDescription": chat.get("groupDescription", ""),
            "latestMessage": chat.get("latestMessage")
        }

        # 5️⃣ Group chat details
        if chat["isGroupChat"]:
            response_data["totalMembers"] = len(users)
            response_data["groupAdmin"] = chat.get("groupAdmin")
            response_data["members"] = users

        # 6️⃣ Private chat details
        else:
            other_user = None
            for u in users:
                if u.get("_id") != logged_user_id:
                    other_user = u
                    break
            
            response_data["otherUser"] = {
                "_id": other_user.get("_id") if other_user else None,
                "username": other_user.get("username") if other_user else None,
                "email": other_user.get("email") if other_user else None,
                "profile_picture": other_user.get("profile_picture") if other_user else None,
                "isOnline": other_user.get("isOnline") if other_user else False,
                "lastSeen": other_user.get("lastSeen") if other_user else None
            }
            # For backward compatibility with what might be expected
            response_data["user"] = response_data["otherUser"]

        return {
            "success": True,
            "chat": response_data
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        print("Error fetching chat details:", e)
        raise HTTPException(status_code=500, detail="Internal server error")

async def remove_user_from_group_controller(request: Request, logged_user_id: str):
    try:

        data = await request.json()
        chat_id = data.get("chat_id")
        user_id = data.get("user_id")

        if not chat_id or not user_id:
            raise HTTPException(status_code=400, detail="Chat ID and User ID are required")

        # 2️⃣ Fetch chat
        chat = await db.chats.find_one({"_id": ObjectId(chat_id)})

        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        # 3️⃣ Check if user is admin
        if chat["groupAdmin"] != ObjectId(logged_user_id):
            raise HTTPException(status_code=403, detail="You are not authorized to remove users from this chat")

        # 4️⃣ Remove user
        chat["users"].remove(ObjectId(user_id))

        # 5️⃣ Update chat
        await db.chats.update_one({"_id": ObjectId(chat_id)}, {"$set": {"users": chat["users"]}})

        # 6️⃣ Fetch and populate chat
        full_chat = await db.chats.find_one({"_id": ObjectId(chat_id)})
        full_chat = await populate_chat_data(full_chat)

        return {
            "success": True,
            "chat": full_chat
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        print("Error removing user from group:", e)
        raise HTTPException(status_code=500, detail="Internal server error")


