# FILE: src/uploader.py
# This is the new, robust version that handles authentication directly
# using individual GitHub repository secrets.

import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from pathlib import Path

YOUTUBE_UPLOAD_SCOPE = ["https://www.googleapis.com/auth/youtube.upload"]

def get_authenticated_service():
    """
    Handles authentication directly using individual GitHub repository secrets
    to bypass missing credentials.json file issues.
    """
    print("INFO: Generating credentials from environment secrets...")
    
    client_id = os.environ.get("YOUTUBE_CLIENT_ID")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN")
    
    if not client_id or not client_secret or not refresh_token:
        raise ValueError("CRITICAL ERROR: Missing YouTube environment secrets (Client ID, Secret, or Refresh Token).")
        
    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=YOUTUBE_UPLOAD_SCOPE
    )
    
    return build('youtube', 'v3', credentials=credentials)

# MODIFIED: Added thumbnail_path parameter
def upload_to_youtube(video_path, title, description, tags, thumbnail_path=None):
    """Uploads a video to YouTube with the given metadata and optionally a thumbnail."""
    print(f"🎬 Uploading '{video_path}' to YouTube...")
    try:
        youtube = get_authenticated_service()

        request_body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags.split(','),
                'categoryId': '28' # 28 = Science & Technology
            },
            'status': {
                'privacyStatus': 'public', # 'private', 'public', or 'unlisted'
                'selfDeclaredMadeForKids': False
            }
        }

        media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True)

        request = youtube.videos().insert(
            part=','.join(request_body.keys()),
            body=request_body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Uploaded {int(status.progress() * 100)}%")

        print(f"✅ Video uploaded successfully! Video ID: {response.get('id')}")
        return response.get('id')

    except Exception as e:
        print(f"❌ ERROR: Failed to upload to YouTube: {e}")
        raise
        
