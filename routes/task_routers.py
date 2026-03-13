from fastapi import APIRouter, Request, Body
from controllers.task_controller import (
    add_task_controller, get_tasks_controller, 
    update_task_controller, delete_task_controller,
    mark_as_completed_controller
)
from models.task_model import TaskCreate, TaskUpdate

router = APIRouter(prefix="/task")

@router.post("/add-task")
async def add_task(data: TaskCreate, request: Request):
    return await add_task_controller(data, request)

@router.get("/get-tasks")
async def get_tasks(request: Request):
    return await get_tasks_controller(request)

@router.post("/update-task")
async def update_task(data: TaskUpdate, request: Request):
    return await update_task_controller(data, request)

@router.post("/delete-task")
async def delete_task(request: Request, body: dict = Body(...)):
    task_id = body.get("id")
    return await delete_task_controller(task_id, request)

@router.post("/mark-as-completed")
async def mark_as_completed(request: Request, body: dict = Body(...)):
    task_id = body.get("id")
    return await mark_as_completed_controller(task_id, request)
