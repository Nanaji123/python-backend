from fastapi import APIRouter, Request, Form, File, UploadFile
from controllers.chat_controller import list_user_controller, get_chats_controller, create_chat_controller, update_chat_controller, delete_chat_controller, get_messages_controller, create_group_chat_controller, get_chat_details_controller, remove_user_from_group_controller

router = APIRouter(prefix="/chat")

@router.get("/list-users")
async def list_user(request: Request, page: int = 1, limit: int = 20, search: str = ""):
    return await list_user_controller(request, page, limit, search)

@router.get("/get-chats")
async def get_chats(request: Request):
    return await get_chats_controller(request)

@router.post("/create-chat")
async def create_chat(request: Request):
    return await create_chat_controller(request)

@router.put("/update-chat")
async def update_chat(request: Request):
    return await update_chat_controller(request)

@router.post("/delete-chat")
async def delete_chat(request: Request):
    return await delete_chat_controller(request)

@router.get("/get-messages/{chat_id}")
async def get_messages(request: Request, chat_id: str, page: int = 1, limit: int = 30):
    return await get_messages_controller(request, chat_id, page, limit)

@router.post("/create-group-chat")
async def create_group_chat(
    request: Request,
    users: str = Form(...),
    groupName: str = Form(...),
    groupDescription: str = Form(""),
    image: UploadFile = File(None)
):
    return await create_group_chat_controller(
        request,
        users,
        groupName,
        groupDescription,
        image
    )

@router.get("/get-chat-details/{chat_id}")
async def get_chat_details(request: Request, chat_id: str):
    return await get_chat_details_controller(request, chat_id)


@router.post("/remove-user-from-group")
async def remove_user_from_group(request: Request):
    return await remove_user_from_group_controller(request)
