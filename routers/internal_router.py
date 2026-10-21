import os
import hmac
from fastapi import APIRouter, BackgroundTasks, Header, HTTPException
from gmail_client import run_scan_for_all_users
from dotenv import load_dotenv

load_dotenv()
router = APIRouter(prefix="/internal", tags=["Internal"])

def scan_job():
    summary = run_scan_for_all_users()
    errors = [s for s in summary if "error" in s]
    print(f"Scan finished: {len(summary)} users with activity, {len(errors)} errors")

@router.post("/run-scan")
def run_scan(background_tasks: BackgroundTasks, x_cron_secret: str = Header(...)):
    if not hmac.compare_digest(x_cron_secret, os.getenv("CRON_SECRET", "")):
        raise HTTPException(status_code=403, detail="Forbidden")
    background_tasks.add_task(scan_job)
    return {"ran": True, "started": True}