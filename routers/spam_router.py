from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from dependencies import get_current_user
from gmail_client import list_spam_messages, trash_messages, delete_messages_permanently, filter_messages
from typing import Optional
from firebase_client import log_activity


router = APIRouter(prefix="/api/spam", tags=["Spam"])

class MessageIdsRequest(BaseModel):
    message_ids: list[str]
@router.get("")
def get_spam_messages(keyword:Optional[str] = None,
                      sender_contains:Optional[str] = None,
                         email:str=Depends(get_current_user),   ):
    messages = list_spam_messages(email, max_results=15)
    if keyword:
        messages = filter_messages(messages, keyword=keyword, sender_contains=sender_contains)
    return {
        "count": len(messages),
        "messages": messages
    }

@router.delete("/permanent")
def permanently_delete_spam(payload: MessageIdsRequest, email: str = Depends(get_current_user)):
    try:
        deleted = delete_messages_permanently(email, payload.message_ids)
        return {"deleted_count": len(deleted), "deleted_ids": deleted}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

from firebase_client import log_activity

@router.post("/trash")
def trash_spam(payload: MessageIdsRequest, email: str = Depends(get_current_user)):
    trashed = trash_messages(email, payload.message_ids)
    log_activity(email, "trashed", len(trashed), trashed)
    return {"trashed_count": len(trashed), "trashed_ids": trashed}