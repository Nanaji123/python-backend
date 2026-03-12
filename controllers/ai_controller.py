from fastapi import HTTPException
from config.gemini import generate_gemini_response


async def gemini_chat_controller(data):

    message = data.message

    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    try:

        ai_reply = await generate_gemini_response(message)

        return {
            "success": True,
            "reply": ai_reply
        }

    except Exception as e:
        print("Gemini AI Error:", e)
        raise HTTPException(status_code=500, detail="AI response failed")   