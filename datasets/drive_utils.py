import io
import json

from django.conf import settings
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

SCOPES = ['https://www.googleapis.com/auth/drive']


def get_drive_service():
    creds = Credentials.from_authorized_user_file(
        str(settings.GOOGLE_DRIVE_TOKEN_FILE), SCOPES
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # persist the refreshed token back to disk
        with open(settings.GOOGLE_DRIVE_TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)


def upload_file_to_drive(file_obj, filename, mimetype):
    service = get_drive_service()
    file_metadata = {
        'name': filename,
        'parents': [settings.GOOGLE_DRIVE_FOLDER_ID],
    }
    media = MediaIoBaseUpload(file_obj, mimetype=mimetype, resumable=True)
    uploaded = service.files().create(
        body=file_metadata, media_body=media, fields='id, name'
    ).execute()
    return uploaded


def download_file_from_drive(file_id):
    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    buffer.seek(0)
    return buffer