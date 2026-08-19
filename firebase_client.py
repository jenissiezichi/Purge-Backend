import firebase_admin
from firebase_admin import credentials, firestore
import os

cred_path = "/etc/secrets/firebase_credentials.json" if os.path.exists("/etc/secrets/firebase_credentials.json") else "firebase_credentials.json"
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)

db = firestore.client()

def save_user_token(email:str, token_data:dict):
    db_collection = db.collection("users").document(email).set(token_data)

def get_user_token(email:str):
    doc = db.collection("users").document(email).get()
    if doc.exists:
        return doc.to_dict()
    return None

def save_oauth_state(state:str, code_verifier:str, scopes:list[str]):
    db.collection("oauth_states").document(state).set({
        "code_verifier": code_verifier,
        "scopes": scopes,
        "created_at": firestore.SERVER_TIMESTAMP,
    })

def get_oauth_state(state:str):
    doc = db.collection("oauth_states").document(state).get()

    if doc.exists:
        return doc.to_dict()
    return None

def delete_oauth_state(state:str):
    db.collection("oauth_states").document(state).delete()

def log_activity(email: str, action: str, count: int, message_ids: list[str]):
    db.collection("activity_logs").add({
        "email": email,
        "action": action,
        "count": count,
        "message_ids": message_ids,
        "timestamp": firestore.SERVER_TIMESTAMP,
    })

def get_recent_activity(email: str, limit: int = 10):
    docs = (
        db.collection("activity_logs")
        .where("email", "==", email)
        .order_by("timestamp", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )
    return [doc.to_dict() for doc in docs]

def create_rule(email: str, keyword: str | None, sender_contains: str | None):
    doc_ref = db.collection("rules").document()
    doc_ref.set({
        "email": email,
        "keyword": keyword,
        "sender_contains": sender_contains,
        "created_at": firestore.SERVER_TIMESTAMP,
    })
    return doc_ref.id

def get_rules(email: str):
    docs = db.collection("rules").where("email", "==", email).stream()
    return [{"id": doc.id, **doc.to_dict()} for doc in docs]

def delete_rule(email: str, rule_id: str):
    doc_ref = db.collection("rules").document(rule_id)
    doc = doc_ref.get()
    if doc.exists and doc.to_dict().get("email") == email:
        doc_ref.delete()
        return True
    return False

def get_all_users():
    docs = db.collection("users").stream()
    return [{"email": doc.id, **doc.to_dict()} for doc in docs]