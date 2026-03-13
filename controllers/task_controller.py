from fastapi import HTTPException, Request
from utils.database import db
from jose import jwt, JWTError
from bson import ObjectId
from datetime import datetime
import os
from models.task_model import TaskCreate, TaskUpdate

SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"

async def get_user_from_request(request: Request):
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        decoded_token = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = decoded_token.get("id")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def add_task_controller(data: TaskCreate, request: Request):
    user_id = await get_user_from_request(request)
    new_task = {
        "userId": user_id,
        "title": data.title,
        "description": data.description,
        "due_date": data.due_date,
        "priority": data.priority,
        "category": data.category,
        "status": "Pending",
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }
    result = await db.tasks.insert_one(new_task)
    return {
        "success": True,
        "message": "Task added successfully",
        "taskId": str(result.inserted_id)
    }

async def get_tasks_controller(request: Request):
    user_id = await get_user_from_request(request)
    tasks = []
    cursor = db.tasks.find({"userId": user_id}).sort("createdAt", -1)
    async for task in cursor:
        tasks.append({
            "id": str(task["_id"]),
            "title": task.get("title"),
            "description": task.get("description"),
            "due_date": task.get("due_date"),
            "priority": task.get("priority"),
            "category": task.get("category"),
            "status": task.get("status"),
            "createdAt": task["createdAt"],
            "updatedAt": task["updatedAt"]
        })
    return {
        "success": True,
        "tasks": tasks
    }

async def update_task_controller(data: TaskUpdate, request: Request):
    user_id = await get_user_from_request(request)
    task_id = data.id
    
    if not ObjectId.is_valid(task_id):
        raise HTTPException(status_code=400, detail="Invalid task ID")
    
    # Filter out None values
    update_data = {k: v for k, v in data.dict(exclude={'id'}).items() if v is not None}
    update_data["updatedAt"] = datetime.utcnow()
    
    result = await db.tasks.update_one(
        {"_id": ObjectId(task_id), "userId": user_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
        
    return {
        "success": True,
        "message": "Task updated successfully"
    }

async def delete_task_controller(task_id: str, request: Request):
    user_id = await get_user_from_request(request)
    
    if not ObjectId.is_valid(task_id):
        raise HTTPException(status_code=400, detail="Invalid task ID")
        
    result = await db.tasks.delete_one({"_id": ObjectId(task_id), "userId": user_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
        
    return {
        "success": True,
        "message": "Task deleted successfully"
    }

async def mark_as_completed_controller(task_id: str, request: Request):
    user_id = await get_user_from_request(request)
    
    if not ObjectId.is_valid(task_id):
        raise HTTPException(status_code=400, detail="Invalid task ID")
        
    result = await db.tasks.update_one(
        {"_id": ObjectId(task_id), "userId": user_id},
        {"$set": {"status": "Completed", "updatedAt": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
        
    return {
        "success": True,
        "message": "Task marked as completed"
    }
