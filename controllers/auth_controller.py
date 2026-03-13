from fastapi import HTTPException, Request, Response,UploadFile, File
from models.user_model import UserChangePassword
from utils.database import db
from utils.hash import hash_password
from utils.validation import validate_username, validate_password
from datetime import datetime, timedelta
from utils.email_service import send_email
from utils.email_templates import verification_email_template, password_reset_email_template
from utils.hash import verify_password
from jose import jwt, JWTError
from bson import ObjectId
import secrets
import random
import os
import math
from config.cloudinary import cloudinary_client
import cloudinary.uploader


SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"

async def register_controller(data):
    username = data.username
    email = data.email
    password = data.password

    if not username or not email or not password:
        raise HTTPException(status_code=400, detail="All fields are required")
    
    if not validate_username(username):
        raise HTTPException(status_code=400, detail="username not invalid")

    if not validate_password(password):
        raise HTTPException(status_code=400, detail="invalid password")

    existing_user= await db.users.find_one({"email": email})

    if existing_user:
        raise HTTPException(status_code=400, detail="user already exists")

    hashed_pwd = hash_password(password)
    
    new_user ={
        "username":username,
        "email":email,
        "password":hashed_pwd,
        "profile_picture": "https://api.dicebear.com/7.x/avataaars/svg?seed=" + username,
        "isVerified":False,
        "isOnline": False,
        "lastSeen": datetime.utcnow(),
        "createdAt":datetime.utcnow(),
        "updatedAt":datetime.utcnow(),
    }

    result = await db.users.insert_one(new_user)

    user_id = str(result.inserted_id)

    await db.passwords.insert_one({
        "userId":user_id,
        "password": hashed_pwd,
        "createdAt": datetime.utcnow()
    })

    token = secrets.token_hex(32)

    await db.tokens.insert_one({
        "userId": user_id,
        "token": hash_password(token),
        "type": "VERIFICATION",
        "expiresAt": datetime.utcnow() + timedelta(hours=1)
    })

    verification_link = f"http://localhost:8000/auth/verify/{user_id}/{token}"

    await send_email(
        to=email,
        subject="Verify your email",
        html=verification_email_template(username, verification_link)
    )

    return {
        "success": True,
        "message": "Verification email sent"
    }


async def verify_controller(user_id: str, token: str):

    # validate ObjectId
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user id")

    # find token document
    token_doc = await db.tokens.find_one({
        "userId": user_id,
        "type": "VERIFICATION",
        "expiresAt": {"$gt": datetime.utcnow()}
    })

    if not token_doc:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification token"
        )

    # compare raw token with hashed token
    is_match = verify_password(token, token_doc.get("token"))

    if not is_match:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification token"
        )

    # find user
    user = await db.users.find_one({"_id": ObjectId(user_id)})

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # update user verification
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"isVerified": True}}
    )

    # delete used token
    await db.tokens.delete_one({"_id": token_doc["_id"]})

    return {
        "success": True,
        "message": "Email verified successfully"
    }


async def login_controller(data, request:Request, response:Response):

    email = data.email
    password = data.password

    if not email or not password:
        raise HTTPException(status_code=400, detail="All fields are required")

    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    
    if not user.get("isVerified"):
        raise HTTPException(status_code=400, detail="User is not verified")

    if user.get("lockUntil") and user["lockUntil"] > datetime.utcnow():
        remaining_minutes = math.ceil((user["lockUntil"] - datetime.utcnow()).total_seconds() / 60)
        raise HTTPException(status_code=403, detail=f"Account is temporarily locked. Try again in {remaining_minutes} minutes.")

    if not verify_password(password, user["password"]):
        loginAttempts = user.get("loginAttempts", 0) + 1

        update_data = {"loginAttempts": loginAttempts}

        if loginAttempts >= 5:
            update_data["lockUntil"] = datetime.utcnow() + timedelta(minutes=15)
        
        await db.users.update_one({"_id": user["_id"]}, {"$set": update_data})
        raise HTTPException(status_code=400, detail="Invalid password")
    
    user["loginAttempts"] = 0
    user["lockUntil"] = None
    user["isOnline"] = True
    user["lastSeen"] = datetime.utcnow()
    await db.users.update_one({"_id": user["_id"]}, {"$set": {"loginAttempts": 0, "lockUntil": None, "isOnline": True, "lastSeen": user["lastSeen"]}})

    user_id_str = str(user["_id"])

    access_token = jwt.encode({
        "id": user_id_str,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }, SECRET_KEY, algorithm=ALGORITHM)
    
    refresh_token = jwt.encode({
        "id": user_id_str,
        "exp": datetime.utcnow() + timedelta(days=7)
    }, SECRET_KEY, algorithm=ALGORITHM)
    
    if user.get("is2FAEnabled"):
        two_fa_code = str(random.randint(100000, 999999))
        await db.tokens.insert_one({
            "user_id": str(user["_id"]),
            "token": two_fa_code,
            "type": "2FA",
            "expires_at": datetime.utcnow() + timedelta(minutes=10)
        })
        await send_email(
            to=user["email"],
            subject="Your 2FA Code",
            html=f"Your 2FA code is: <strong>{two_fa_code}</strong>. It will expire in 10 minutes."
        )
        return {
            "success": True,
            "two_fa_required": True,
            "message": "2FA code sent to your email."
        }
    
    response.set_cookie("access_token", access_token, httponly=True, secure=True, samesite="strict", max_age=3600)
    response.set_cookie("refresh_token", refresh_token, httponly=True, secure=True, samesite="strict", max_age=604800)

    # Store session
    await db.sessions.insert_one({
        "userId": user_id_str,
        "refreshToken": hash_password(refresh_token),
        "createdAt": datetime.utcnow()
    })
    return {
        "success": True,
        "user": {
            "username": user["username"],
            "email": user["email"],
            "profile_picture": user.get("profile_picture") or "https://api.dicebear.com/7.x/avataaars/svg?seed=" + user["username"],
            "isOnline": user.get("isOnline") or False,
            "lastSeen": user.get("lastSeen") or datetime.utcnow()
        }
    }


async def logout_controller(request: Request, response: Response):

    refresh_token = request.cookies.get("refresh_token")

    if refresh_token:
        try:
            decoded_token = jwt.decode(
                refresh_token,
                SECRET_KEY,
                algorithms=[ALGORITHM]
            )

            user_id = decoded_token.get("id")

            sessions = db.sessions.find({"userId": user_id})

            async for session in sessions:
                if verify_password(refresh_token, session["refreshToken"]):
                    await db.sessions.delete_one({"_id": session["_id"]})
                    break

        except JWTError:
            # token invalid or expired
            pass

    # clear cookies
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return {
        "success": True,
        "message": "Logout successful"
    }


async def forget_password_controller(email: str):

    try:
        user = await db.users.find_one({"email": email})

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        reset_token_raw = secrets.token_hex(32)

        await db.tokens.delete_many({
            "userId": str(user["_id"]),
            "type": "PASSWORD_RESET"
        })

        hashed_token = hash_password(reset_token_raw)

        await db.tokens.insert_one({
            "userId": str(user["_id"]),
            "token": hashed_token,
            "type": "PASSWORD_RESET",
            "expiresAt": datetime.utcnow() + timedelta(minutes=15)
        })

        reset_link = f"http://localhost:3000/reset-password/{str(user['_id'])}/{reset_token_raw}"

        await send_email(
            to=user["email"],
            subject="Reset your password",
            html=password_reset_email_template(user["username"], reset_link)
        )

        return {
            "success": True,
            "message": "Password reset email sent"
        }

    except Exception as e:
        print("Error in forget password:", e)
        raise HTTPException(status_code=500, detail="Internal server error")


async def reset_password_controller(user_id: str, token: str, new_password: str):

    # 1️⃣ Validate password
    if not new_password:
        raise HTTPException(status_code=400, detail="Password is required")

    if not validate_password(new_password):
        raise HTTPException(status_code=400, detail="Invalid password")

    # 2️⃣ Find reset token
    token_doc = await db.tokens.find_one({
        "userId": user_id,
        "type": "PASSWORD_RESET",
        "expiresAt": {"$gt": datetime.utcnow()}
    })

    if not token_doc:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token"
        )

    # 3️⃣ Verify hashed token
    is_match = verify_password(token, token_doc["token"])

    if not is_match:
        raise HTTPException(
            status_code=400,
            detail="Invalid reset token"
        )

    # 4️⃣ Find user
    user = await db.users.find_one({"_id": ObjectId(user_id)})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 5️⃣ Check password history
    password_history = db.passwords.find({"userId": user_id})

    async for old_password in password_history:
        if verify_password(new_password, old_password["password"]):
            raise HTTPException(
                status_code=400,
                detail="Password already used"
            )

    # 6️⃣ Hash new password
    hashed_password = hash_password(new_password)

    # 7️⃣ Update user password and reset security fields
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "password": hashed_password,
            "loginAttempts": 0,
            "lockUntil": None,
            "updatedAt": datetime.utcnow()
        }}
    )

    # 8️⃣ Save password history
    await db.passwords.insert_one({
        "userId": user_id,
        "password": hashed_password,
        "createdAt": datetime.utcnow()
    })

    # 9️⃣ Delete reset token
    await db.tokens.delete_one({"_id": token_doc["_id"]})

    # 🔟 Revoke all sessions
    await db.sessions.delete_many({"userId": user_id})

    return {
        "success": True,
        "message": "Password reset successful. All active sessions logged out."
    }


async def change_password_controller(request: Request, data: UserChangePassword):
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        decoded_token = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = decoded_token.get("id")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    current_password = data.current_password
    new_password = data.new_password
        
    if not verify_password(current_password, user["password"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    if not validate_password(new_password):
        raise HTTPException(status_code=400, detail="New password does not meet complexity requirements")
    
    password_history = db.passwords.find({"userId": user_id})
    async for password_doc in password_history:
        if verify_password(new_password, password_doc["password"]):
            raise HTTPException(status_code=400, detail="Password already used")

    hashed_password = hash_password(new_password)
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "password": hashed_password,
            "updatedAt": datetime.utcnow()
        }}
    )
    await db.passwords.insert_one({
        "userId": user_id,
        "password": hashed_password,
        "createdAt": datetime.utcnow()
    })

    current_refresh_token = request.cookies.get("refresh_token")
    if current_refresh_token:
        sessions = db.sessions.find({"userId": user_id})
        async for session in sessions:
            if not verify_password(current_refresh_token, session["refreshToken"]):
                await db.sessions.delete_one({"_id": session["_id"]})

    return {
        "success": True,
        "message": "Password updated successfully. Other devices logged out."
    }



async def delete_user_controller(request: Request):
    user_id = request.user.get("id")
    await db.users.delete_one({"_id": ObjectId(user_id)})
    return {
        "success": True,
        "message": "User deleted successfully"
    }





async def me_controller(request: Request):
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        decoded_token = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = decoded_token.get("id")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "success": True,
        "user": {
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"],
            "profile_picture": user.get("profile_picture") or "https://api.dicebear.com/7.x/avataaars/svg?seed=" + user["username"],
            "createdAt": user.get("createdAt") or datetime.utcnow(),
            "updatedAt": user.get("updatedAt") or datetime.utcnow()
        }
    }


async def change_username_controller(request: Request, new_username: str):
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        decoded_token = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = decoded_token.get("id")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    username_change_count = user.get("usernamechangeCount", 5)
    if username_change_count <= 0:
        raise HTTPException(status_code=400, detail="Username change limit reached")
    if not validate_username(new_username):
        raise HTTPException(status_code=400, detail="Invalid username")
    if await db.users.find_one({"username": new_username}):
        raise HTTPException(status_code=400, detail="Username already exists")
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "username": new_username,
            "usernamechangeCount": username_change_count - 1,
            "updatedAt": datetime.utcnow()
        }}
    )
    return {
        "success": True,
        "message": "Username changed successfully"
    }

async def update_profile_picture_controller(request: Request, image: UploadFile = File(...)):
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        decoded_token = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = decoded_token.get("id")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.get("profile_picture") and "dicebear.com" not in user["profile_picture"]:
        try:
            public_id = user["profile_picture"].split("/")[-1].split(".")[0]
            cloudinary.uploader.destroy(f"profile_pictures/{public_id}")
        except Exception as e:
            print("Cloudinary delete error:", e)
    result = cloudinary.uploader.upload(image.file, folder="profile_pictures")
    image_url = result["secure_url"]
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"profile_picture": image_url, "updatedAt": datetime.utcnow()}}
    )
    return {
        "success": True,
        "message": "Profile picture updated successfully",
        "profile_picture": image_url
    }

 