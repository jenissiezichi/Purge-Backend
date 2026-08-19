import os
from fastapi import APIRouter, Header, HTTPException
from gmail_client import run_scan_for_all_users
from dotenv import load_dotenv

load_dotenv()
router = APIRouter(prefix="/internal", tags=["Internal"])

@router.post("/run-scan")
def run_scan(x_cron_secret: str = Header(...)):
    print("Expected:", os.getenv("CRON_SECRET"))
    print("Received:", x_cron_secret)
    if x_cron_secret != os.getenv("CRON_SECRET"):
        raise HTTPException(status_code=403, detail="Forbidden")
    summary = run_scan_for_all_users()
    return {"ran": True, "summary": summary}