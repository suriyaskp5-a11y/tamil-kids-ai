import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from app.core.config import settings

logger = logging.getLogger("TamilKidsAI.YouTubeService")

class YouTubeService:
    def __init__(self):
        self.client_secrets_file = settings.YOUTUBE_CLIENT_SECRETS_FILE
        self.token_file = settings.YOUTUBE_OAUTH_TOKEN_FILE

    def is_authenticated(self) -> bool:
        return os.path.exists(self.token_file)

    def get_auth_url(self) -> Optional[str]:
        """Generates Google OAuth 2.0 authorization URL for YouTube Data API v3."""
        if not os.path.exists(self.client_secrets_file):
            logger.warning(f"client_secrets.json not found at {self.client_secrets_file}")
            return None
            
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow
            scopes = ["https://www.googleapis.com/auth/youtube.upload"]
            flow = InstalledAppFlow.from_client_secrets_file(self.client_secrets_file, scopes)
            flow.redirect_uri = "http://localhost:8000/api/v1/youtube/oauth2callback"
            auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
            return auth_url
        except Exception as e:
            logger.error(f"Failed to generate OAuth URL: {e}")
            return None

    def upload_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: Optional[List[str]] = None,
        thumbnail_path: Optional[str] = None,
        privacy_status: str = "private",
        made_for_kids: bool = True
    ) -> Dict[str, Any]:
        """
        Uploads a video to YouTube using resumable chunked upload.
        Enforces Made For Kids policies.
        """
        if not os.path.exists(self.token_file):
            return {
                "success": False,
                "error": "YouTube OAuth token not configured. Please complete OAuth authorization first."
            }

        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload

            creds = Credentials.from_authorized_user_file(self.token_file)
            youtube = build("youtube", "v3", credentials=creds)

            # Metadata body
            body = {
                "snippet": {
                    "title": title[:100],
                    "description": description[:5000],
                    "tags": tags or ["Tamil Kids Stories", "Moral Stories", "Tamil Cartoons"],
                    "categoryId": "27"  # Education / Kids
                },
                "status": {
                    "privacyStatus": privacy_status,
                    "selfDeclaredMadeForKids": made_for_kids,
                    "embeddable": True
                }
            }

            media = MediaFileUpload(
                video_path,
                chunksize=1024*1024*4, # 4MB chunks
                resumable=True,
                mimetype="video/mp4"
            )

            request = youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    logger.info(f"YouTube upload progress: {progress}%")

            video_id = response.get("id")
            logger.info(f"Successfully uploaded video to YouTube: ID={video_id}")

            # Upload custom thumbnail if provided
            if thumbnail_path and os.path.exists(thumbnail_path) and video_id:
                try:
                    youtube.thumbnails().set(
                        videoId=video_id,
                        media_body=MediaFileUpload(thumbnail_path, mimetype="image/jpeg")
                    ).execute()
                    logger.info(f"Custom thumbnail attached to video {video_id}")
                except Exception as thumb_err:
                    logger.warning(f"Could not set custom thumbnail (channel may need verification): {thumb_err}")

            return {
                "success": True,
                "video_id": video_id,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "privacy_status": privacy_status,
                "made_for_kids": made_for_kids
            }

        except Exception as e:
            logger.error(f"YouTube upload error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
