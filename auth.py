import os
from dotenv import load_dotenv
from google_auth_oauthlib.flow import Flow
import requests
from firebase_client import save_oauth_state, get_oauth_state, delete_oauth_state

load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URL = os.getenv("GOOGLE_REDIRECT_URL")

BASE_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid"
]

FULL_DELETE_SCOPE = "https://mail.google.com/"

def _build_flow(scopes: list[str], code_verifier: str = None):
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [GOOGLE_REDIRECT_URL],
            }
        },
        scopes=scopes,
        redirect_uri=GOOGLE_REDIRECT_URL,
    )
    if code_verifier:
        flow.code_verifier = code_verifier
    return flow

def get_google_auth(extra_scopes: list[str] = None):
    scopes = BASE_SCOPES + (extra_scopes or [])
    flow = _build_flow(scopes)

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    # Save the PKCE verifier + scopes in Firestore, keyed by state
    save_oauth_state(state, flow.code_verifier, scopes)

    return authorization_url

def exchange_code_for_token(code: str, state: str):
    entry = get_oauth_state(state)
    if entry is None:
        raise ValueError("Invalid or expired state — try logging in again.")

    flow = _build_flow(entry["scopes"], code_verifier=entry["code_verifier"])
    flow.fetch_token(code=code)
    credentials = flow.credentials

    delete_oauth_state(state)  # clean up, one-time use

    return {
        "access_token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
        "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
    }

def get_user_email(access_token):
    response = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    response.raise_for_status()
    return response.json()["email"]