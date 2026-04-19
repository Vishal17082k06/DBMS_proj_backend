import os
import json
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from dotenv import load_dotenv

# Load .env from project root
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".env")
load_dotenv(dotenv_path)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCOPES = ["https://www.googleapis.com/auth/calendar"]
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")

import hashlib
import base64

# Use a fixed verifier for local development to avoid PKCE state loss
FIXED_VERIFIER = "this_is_a_fixed_verifier_for_local_development_testing_123"
code_challenge = base64.urlsafe_b64encode(hashlib.sha256(FIXED_VERIFIER.encode()).digest()).decode().replace("=", "")

def get_flow():
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
    print(f"\n[DEBUG] Flow using Redirect URI: {redirect_uri}\n")
    return Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )

def get_auth_url():
    flow = get_flow()
    # Manually pass the challenge to Google
    auth_url, _ = flow.authorization_url(
        prompt="consent",
        code_challenge=code_challenge,
        code_challenge_method="S256"
    )
    return auth_url

def exchange_code_for_token(code: str):
    flow = get_flow()
    # Use the same fixed verifier to exchange the code
    flow.fetch_token(code=code, code_verifier=FIXED_VERIFIER)
    creds = flow.credentials
    # Save token to file so you don't need to login again
    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())

def get_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    # Auto-refresh if expired
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds