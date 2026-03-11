from utils.hash import verify_password


async def compare_token(raw_token: str, hashed_token: str):

    return verify_password(raw_token, hashed_token)