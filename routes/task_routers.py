from fastapi import APIRouter, Request, Body
from controllers.task_controller import (
    add_task_controller, get_tasks_controller, 
    update_task_controller, delete_task_controller,
    mark_as_completed_controller
)
from models.task_model import TaskCreate, TaskUpdate
from fastapi import Depends
from utils.auth_deps import get_current_user

router = APIRouter(prefix="/task")

@router.post("/add-task")
async def add_task(data: TaskCreate, user_id: str = Depends(get_current_user)):
    return await add_task_controller(data, user_id)

@router.get("/get-tasks")
async def get_tasks(user_id: str = Depends(get_current_user)):
    return await get_tasks_controller(user_id)

@router.post("/update-task")
async def update_task(data: TaskUpdate, user_id: str = Depends(get_current_user)):
    return await update_task_controller(data, user_id)

@router.post("/delete-task")
async def delete_task(user_id: str = Depends(get_current_user), body: dict = Body(...)):
    task_id = body.get("id")
    return await delete_task_controller(task_id, user_id)

@router.post("/mark-as-completed")
async def mark_as_completed(user_id: str = Depends(get_current_user), body: dict = Body(...)):
    task_id = body.get("id")
    return await mark_as_completed_controller(task_id, user_id)
