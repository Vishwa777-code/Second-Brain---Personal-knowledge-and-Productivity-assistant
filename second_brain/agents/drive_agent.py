"""
Optional stretch — Google Drive Toolkit.

Requires the same Google Cloud OAuth project you'd set up for the full
Gmail API option (see README.md). Reuses a client_secret.json + token flow.
Kept separate from the core app so the app still runs fine if you never
set this up.
"""
import os
import pickle
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
TOKEN_PATH = "data/drive_token.pickle"


def _get_drive_service(client_secret_file: str = "client_secret.json"):
    creds = None
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "rb") as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
            creds = flow.run_local_server(port=0)
        os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
        with open(TOKEN_PATH, "wb") as f:
            pickle.dump(creds, f)
    return build("drive", "v3", credentials=creds)


def upload_report(file_path: str, filename: str = None) -> str:
    try:
        service = _get_drive_service()
        file_metadata = {"name": filename or os.path.basename(file_path)}
        media = MediaFileUpload(file_path, resumable=True)
        uploaded = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
        return f"Uploaded to Drive. File ID: {uploaded.get('id')}"
    except Exception as e:
        return f"Drive upload failed (is client_secret.json set up? see README): {e}"


def search_drive_files(query: str) -> str:
    try:
        service = _get_drive_service()
        results = service.files().list(q=f"name contains '{query}'", fields="files(id, name)").execute()
        files = results.get("files", [])
        return "\n".join(f"{f['name']} ({f['id']})" for f in files) or "No matching files found."
    except Exception as e:
        return f"Drive search failed: {e}"
