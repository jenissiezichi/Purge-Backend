from fastapi import FastAPI, APIRouter, Depends, Request
from rate_limiter import limiter
from auth import get_google_auth, exchange_code_for_token, get_user_email, FULL_DELETE_SCOPE
from firebase_client import save_user_token
from utils.jwt_utils import create_access_token
from dependencies import get_current_user
from fastapi.responses import RedirectResponse
import os

FRONTEND_URL = os.getenv("https://purge-it.vercel.app", "http://localhost:5174")

router = APIRouter(prefix="/auth/google", tags=["auth"])

@router.get("")
@limiter.limit("5/minute")
def google_auth(request:Request):
    return {
        "auth_url": get_google_auth()
    }

@router.get("/callback")

def google_auth_callback(code: str, state: str):
    token_data = exchange_code_for_token(code, state)
    email = get_user_email(token_data["access_token"])
    save_user_token(email, token_data)
    jwt_token = create_access_token(email)
    return RedirectResponse(url=f"{FRONTEND_URL}/auth/callback?token={jwt_token}&email={email}")

@router.get("/upgrade/permanent_delete")
def request_permanent_delete(email:str = Depends(get_current_user)):
    return {"auth_url":get_google_auth(extra_scopes=[FULL_DELETE_SCOPE])}