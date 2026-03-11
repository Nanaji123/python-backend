from fastapi import APIRouter, Request, Response
from controllers.auth_controller import register_controller, login_controller, verify_controller, logout_controller, forget_password_controller, reset_password_controller, change_password_controller
from models.user_model import UserRegister, UserLogin, UserChangePassword
from fastapi import Body


router = APIRouter(prefix="/auth")


@router.post("/register")
async def register(user: UserRegister):
    return await register_controller(user)


@router.get("/verify/{user_id}/{token}")
async def verify(user_id: str, token: str):
    return await verify_controller(user_id, token)


@router.post("/login")
async def login(user: UserLogin, request: Request, response: Response):
    return await login_controller(user, request, response)


@router.post("/logout")
async def logout(request: Request, response: Response):
    return await logout_controller(request, response)

@router.post("/forgot-password")
async def forgot_password(email: str = Body(..., embed=True)):
    return await forget_password_controller(email)


@router.post("/reset-password/{user_id}/{token}")
async def reset_password(user_id: str, token: str, new_password: str = Body(..., embed=True)):
    return await reset_password_controller(user_id, token, new_password)

@router.post("/change-password")
async def change_password(data: UserChangePassword, request: Request):
    return await change_password_controller(request, data)

