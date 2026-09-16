import io

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
        with open(settings.GOOGLE_DRIVE_TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)


def find_or_create_folder(service, folder_name, parent_id):
    safe_name = folder_name.replace("'", "\\'")
    query = (
        f"name = '{safe_name}' and '{parent_id}' in parents "
        "and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    )
    results = service.files().list(q=query, fields='files(id, name)').execute()
    files = results.get('files', [])
    if files:
        return files[0]['id']
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id],
    }
    created = service.files().create(body=folder_metadata, fields='id').execute()
    return created['id']


def resolve_type_variant_folder(file_type, variant):
    service = get_drive_service()
    type_folder_id = find_or_create_folder(service, file_type, settings.GOOGLE_DRIVE_FOLDER_ID)
    variant_folder_id = find_or_create_folder(service, variant, type_folder_id)
    return variant_folder_id


def upload_file_to_drive(file_obj, filename, mimetype, parent_folder_id):
    service = get_drive_service()
    file_metadata = {
        'name': filename,
        'parents': [parent_folder_id],
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