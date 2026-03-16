from controllers.chat_controller import list_user_controller, get_chats_controller, create_chat_controller, update_chat_controller, delete_chat_controller, get_messages_controller, create_group_chat_controller, get_chat_details_controller, remove_user_from_group_controller
from fastapi import Depends
from utils.auth_deps import get_current_user
from fastapi import APIRouter, Request, Form, File, UploadFile

router = APIRouter(prefix="/chat")

@router.get("/list-users")
async def list_user(page: int = 1, limit: int = 20, search: str = "", user_id: str = Depends(get_current_user)):
    return await list_user_controller(user_id, page, limit, search)

@router.get("/get-chats")
async def get_chats(user_id: str = Depends(get_current_user)):
    return await get_chats_controller(user_id)

@router.post("/create-chat")
async def create_chat(request: Request, user_id: str = Depends(get_current_user)):
    return await create_chat_controller(request, user_id)

@router.put("/update-chat")
async def update_chat(request: Request, user_id: str = Depends(get_current_user)):
    return await update_chat_controller(request, user_id)

@router.post("/delete-chat")
async def delete_chat(request: Request, user_id: str = Depends(get_current_user)):
    return await delete_chat_controller(request, user_id)

@router.get("/get-messages/{chat_id}")
async def get_messages(chat_id: str, page: int = 1, limit: int = 30, user_id: str = Depends(get_current_user)):
    return await get_messages_controller(chat_id, user_id, page, limit)

@router.post("/create-group-chat")
async def create_group_chat(
    users: str = Form(...),
    groupName: str = Form(...),
    groupDescription: str = Form(""),
    image: UploadFile = File(None),
    user_id: str = Depends(get_current_user)
):
    return await create_group_chat_controller(
        user_id,
        users,
        groupName,
        groupDescription,
        image
    )

@router.get("/get-chat-details/{chat_id}")
async def get_chat_details(chat_id: str, user_id: str = Depends(get_current_user)):
    return await get_chat_details_controller(chat_id, user_id)


@router.post("/remove-user-from-group")
async def remove_user_from_group(request: Request, user_id: str = Depends(get_current_user)):
    return await remove_user_from_group_controller(request, user_id)
