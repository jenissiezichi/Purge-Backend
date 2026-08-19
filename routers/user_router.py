from fastapi import APIRouter, Depends
from dependencies import get_current_user
from firebase_client import get_recent_activity, get_user_token

router = APIRouter(prefix="/api", tags=["User"])

@router.get("/me")
def read_current_user(email: str = Depends(get_current_user)):
    token_data = get_user_token(email)
    return {
        "email": email,
        "scopes": token_data.get("scopes", []) if token_data else [],
    }

@router.get("/activity")
def read_recent_activity(email: str = Depends(get_current_user)):
    return {"activity": get_recent_activity(email)}