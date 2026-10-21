from fastapi import APIRouter, Depends, HTTPException
from dependencies import get_current_user
from auth import FULL_DELETE_SCOPE
from firebase_client import get_recent_activity, get_user_token, set_permanent_delete_enabled, get_stats
router = APIRouter(prefix="/api", tags=["User"])

@router.get("/me")
def read_current_user(email: str = Depends(get_current_user)):
    token_data = get_user_token(email)
    return {
        "email": email,
        "scopes": token_data.get("scopes", []) if token_data else [],
        "permanent_delete_enabled": token_data.get("permanent_delete_enabled", True) if token_data else True,
    }

@router.get("/activity")
def read_recent_activity(limit: int = 10, email: str = Depends(get_current_user)):
    return {"activity": get_recent_activity(email, limit=limit)}

@router.post("/permanent-delete/off")
def turn_off_permanent_delete(email: str = Depends(get_current_user)):
    set_permanent_delete_enabled(email, False)
    return {"permanent_delete_enabled": False}

@router.post("/permanent-delete/on")
def turn_on_permanent_delete(email: str = Depends(get_current_user)):
    token_data = get_user_token(email)
    if not token_data or FULL_DELETE_SCOPE not in token_data.get("scopes", []):
        raise HTTPException(status_code=403, detail="Permanent delete access not granted yet.")
    set_permanent_delete_enabled(email, True)
    return {"permanent_delete_enabled": True}

@router.get("/stats")
def read_stats(email: str = Depends(get_current_user)):
    return get_stats(email)