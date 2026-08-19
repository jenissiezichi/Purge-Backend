from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, model_validator
from typing import Optional
from dependencies import get_current_user
from firebase_client import create_rule, get_rules, delete_rule

router = APIRouter(prefix="/api/rules", tags=["Rules"])


class RuleRequest(BaseModel):
    keyword: Optional[str] = None
    sender_contains: Optional[str] = None

    @model_validator(mode="after")
    def at_least_one_field(self):
        if not self.keyword and not self.sender_contains:
            raise ValueError("A rule needs at least a keyword or sender_contains value.")
        return self


@router.get("")
def list_rules(email: str = Depends(get_current_user)):
    return {"rules": get_rules(email)}


@router.post("")
def add_rule(payload: RuleRequest, email: str = Depends(get_current_user)):
    rule_id = create_rule(email, payload.keyword, payload.sender_contains)
    return {"id": rule_id, "keyword": payload.keyword, "sender_contains": payload.sender_contains}


@router.delete("/{rule_id}")
def remove_rule(rule_id: str, email: str = Depends(get_current_user)):
    deleted = delete_rule(email, rule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Rule not found or not yours.")
    return {"deleted": True, "id": rule_id}