from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from auth import FULL_DELETE_SCOPE
from firebase_client import get_user_token, get_rules, log_activity, get_all_users
from datetime import datetime
import time


def get_gmail_services(email:str):
    token_data = get_user_token(email)
    if not token_data:
        raise ValueError("No saved token")

    credentials = Credentials(
       token = token_data["access_token"],
        refresh_token=token_data["refresh_token"],
        token_uri=token_data["token_uri"],
        client_id=token_data["client_id"],
        client_secret=token_data["client_secret"],
        scopes=token_data["scopes"],
        expiry=datetime.fromisoformat(token_data["expiry"]) if token_data.get("expiry") else None,
    )
    service = build("gmail", "v1", credentials=credentials)
    return service

def list_spam_messages(email: str, max_results: int = 10):
    service = get_gmail_services(email)

    results = service.users().messages().list(
        userId="me",
        labelIds=["SPAM"],
        maxResults=max_results
    ).execute()

    messages = results.get("messages", [])
    detailed_messages = []

    def callback(request_id, response, exception):
        if exception is None:
            headers = {h["name"]: h["value"] for h in response["payload"]["headers"]}
            detailed_messages.append({
                "id": response["id"],
                "from": headers.get("From"),
                "subject": headers.get("Subject"),
                "date": headers.get("Date"),
            })

    batch = service.new_batch_http_request(callback=callback)
    for message in messages:
        batch.add(
            service.users().messages().get(
                userId="me",
                id=message["id"],
                format="metadata",
                metadataHeaders=["From", "Subject", "Date"]
            )
        )
    batch.execute()

    return detailed_messages

def trash_messages(email: str, message_ids: list[str]):
    service = get_gmail_services(email)
    results = []
    for msg_id in message_ids:
        service.users().messages().trash(userId="me", id=msg_id).execute()
        results.append(msg_id)
    return results



def delete_messages_permanently(email: str, message_ids: list[str]):
    token_data = get_user_token(email)
    if FULL_DELETE_SCOPE not in token_data.get("scopes", []):
        raise PermissionError("User has not granted permanent delete access yet.")

    service = get_gmail_services(email)
    results = []
    for msg_id in message_ids:
        service.users().messages().delete(userId="me", id=msg_id).execute()
        results.append(msg_id)
    return results

def filter_messages(messages: list[dict], keyword:str = None, sender_contains:str = None):
    filtered = messages
    if keyword:
        keyword_lower = keyword.lower()
        filtered = [
            m for m in filtered
            if keyword_lower in( m.get("subject") or "").lower()
        ]
        if sender_contains:
            sender_lower = sender_contains.lower()
            filtered = [
                m for m in filtered
                if sender_lower in( m.get("subject") or "").lower()
            ]
        return filtered

def run_scan_for_all_users():
    users = get_all_users()
    summary = []

    for user in users:
        email = user["email"]
        try:
            rules = get_rules(email)
            if not rules:
                continue

            spam = list_spam_messages(email, max_results=50)
            matched_ids = set()

            for rule in rules:
                filtered = filter_messages(
                    spam,
                    keyword=rule.get("keyword"),
                    sender_contains=rule.get("sender_contains"),
                )
                matched_ids.update(m["id"] for m in filtered)

            if matched_ids:
                trashed = trash_messages(email, list(matched_ids))
                log_activity(email, "auto-trashed", len(trashed), trashed)
                summary.append({"email": email, "trashed": len(trashed)})
        except Exception as e:
            summary.append({"email": email, "error": str(e)})

    return summary