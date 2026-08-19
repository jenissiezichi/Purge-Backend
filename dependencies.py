from fastapi import HTTPException, Header
from starlette import status
from utils.jwt_utils import decode_token

def get_current_user(authorization:str = Header(...)):
    if not authorization.startswith('Bearer '):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth Headers")

    token = authorization.replace("Bearer ", "")
    email = decode_token(token)
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return email