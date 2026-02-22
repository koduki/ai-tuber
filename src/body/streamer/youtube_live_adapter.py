"""YouTube Live API adapter for creating and managing live streams"""
import os
import json
import logging
from typing import Dict, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

logger = logging.getLogger(__name__)

# YouTube OAuth configuration from environment
YOUTUBE_CLIENT_SECRET_PATH = os.getenv("YOUTUBE_CLIENT_SECRET_PATH", "/secret/google_client_secret.json")
YOUTUBE_TOKEN_PATH = os.getenv("YOUTUBE_TOKEN_PATH", "/secret/yt_token.json")


class YoutubeLiveAdapter:
    """Adapter for YouTube Live API operations"""
    
    def __init__(self) -> None:
        pass

    def authenticate_youtube(self):
        """Authenticate to the YouTube API and return the API client."""
        # Scopes required by the API
        scopes = ["https://www.googleapis.com/auth/youtube"]

        creds = None
        
        # 1. Try to load from environment variable (JSON string) first
        token_json_str = os.getenv("YOUTUBE_TOKEN_JSON")
        if token_json_str:
            try:
                # Remove UTF-8 BOM if present
                if token_json_str.startswith('\ufeff'):
                    token_json_str = token_json_str[1:]
                token_info = json.loads(token_json_str)
                creds = Credentials.from_authorized_user_info(token_info, scopes)
                logger.info("Loaded YouTube credentials from YOUTUBE_TOKEN_JSON environment variable")
            except Exception as e:
                logger.error(f"Failed to load credentials from YOUTUBE_TOKEN_JSON: {e}")

        # 2. Fallback to file if not loaded from env
        if not creds and os.path.exists(YOUTUBE_TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(YOUTUBE_TOKEN_PATH, scopes)
            logger.info(f"Loaded YouTube credentials from {YOUTUBE_TOKEN_PATH}")
        
        # If there are no (valid) credentials available, let the user log in.
        needs_new_flow = True
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing YouTube credentials...")
            try:
                creds.refresh(Request())
                needs_new_flow = False
            except Exception as e:
                logger.warning(f"Failed to refresh YouTube credentials: {e}")
        
        if not creds or not creds.valid or needs_new_flow:
            logger.info("Starting new YouTube OAuth flow...")
            
            flow = None
            # Try to initialize flow from environment variable first
            client_secret_json_str = os.getenv("YOUTUBE_CLIENT_SECRET_JSON")
            if client_secret_json_str:
                try:
                    if client_secret_json_str.startswith('\ufeff'):
                        client_secret_json_str = client_secret_json_str[1:]
                    client_config = json.loads(client_secret_json_str)
                    flow = Flow.from_client_config(
                        client_config,
                        scopes=scopes,
                        redirect_uri='urn:ietf:wg:oauth:2.0:oob')
                    logger.info("Initialized YouTube OAuth flow from YOUTUBE_CLIENT_SECRET_JSON")
                except Exception as e:
                    logger.error(f"Failed to initialize flow from YOUTUBE_CLIENT_SECRET_JSON: {e}")

            # Fallback to file for flow
            if not flow:
                if os.path.exists(YOUTUBE_CLIENT_SECRET_PATH):
                    flow = Flow.from_client_secrets_file(
                        YOUTUBE_CLIENT_SECRET_PATH,
                        scopes=scopes,
                        redirect_uri='urn:ietf:wg:oauth:2.0:oob')
                    logger.info(f"Initialized YouTube OAuth flow from {YOUTUBE_CLIENT_SECRET_PATH}")
                else:
                    raise FileNotFoundError(f"YouTube client secret not found in env or at {YOUTUBE_CLIENT_SECRET_PATH}")
            
            auth_url, _ = flow.authorization_url(prompt='consent')
            
            print('\n' + '='*60)
            print('AUTHORIZATION REQUIRED FOR YOUTUBE LIVE')
            print('Please go to this URL in your browser:')
            print(f'{auth_url}')
            print('='*60 + '\n')
            
            logger.warning(f"Authorization required. Please check container logs and use 'docker attach' to enter the code.")
            
            code = input('Enter the authorization code: ')
            credential = flow.fetch_token(code=code)
            creds = Credentials(
                token=credential['access_token'],
                refresh_token=credential['refresh_token'],
                token_uri=flow.client_config['token_uri'],
                client_id=flow.client_config['client_id'],
                client_secret=flow.client_config['client_secret'],
                scopes=scopes
            )

            # Save the credentials for the next run if a path is provided
            if YOUTUBE_TOKEN_PATH:
                try:
                    os.makedirs(os.path.dirname(YOUTUBE_TOKEN_PATH), exist_ok=True)
                    with open(YOUTUBE_TOKEN_PATH, 'w') as token:
                        token.write(creds.to_json())
                    logger.info(f"Saved refreshed/new credentials to {YOUTUBE_TOKEN_PATH}")
                except Exception as e:
                    logger.warning(f"Could not save tokens to {YOUTUBE_TOKEN_PATH} (continuing anyway): {e}")

        youtube = build('youtube', 'v3', credentials=creds)
        return youtube, creds

    def create_live(self, youtube, title: str, description: str, scheduledStartTime: str, 
                   thumbnail_path: Optional[str] = None, privacy_status: str = "private") -> Dict:
        """
        Create a YouTube Live broadcast with stream configuration.
        
        Args:
            youtube: Authenticated YouTube API client
            title: Broadcast title
            description: Broadcast description
            scheduledStartTime: ISO 8601 format timestamp
            thumbnail_path: Path to thumbnail image (optional)
            privacy_status: Video privacy (private, unlisted, public)
            
        Returns:
            Dictionary containing broadcast, thumbnail, stream, and bind responses
        """
        broadcast_response = self._create_broadcast(youtube, title, description, scheduledStartTime, privacy_status)
        
        thumbnail_response = None
        if thumbnail_path:
            thumbnail_response = self._set_thumbnail(youtube, broadcast_response['id'], thumbnail_path)
        
        stream_response = self._create_stream(youtube, title + "_Stream")
        bind_response = self._bind_broadcast_to_stream(youtube, broadcast_response['id'], stream_response['id'])
        
        return {
            "broadcast": broadcast_response, 
            "thumbnail": thumbnail_response, 
            "stream": stream_response, 
            "bind": bind_response
        }

    def _create_broadcast(self, youtube, title: str, description: str, 
                         scheduledStartTime: str, privacy_status: str = "private") -> Dict:
        """Create a live broadcast on YouTube."""
        res = youtube.liveBroadcasts().insert(
            part="snippet,status,contentDetails",
            body=dict(
                snippet=dict(
                    title=title,
                    description=description,
                    scheduledStartTime=scheduledStartTime
                ),
                contentDetails=dict(
                    enableAutoStart=True,
                    latencyPreference="ultraLow"  # 超低遅延
                ),
                status=dict(
                    privacyStatus=privacy_status
                )
            )
        ).execute()

        logger.info(f"Created broadcast: {res['id']}")
        return res

    def _set_thumbnail(self, youtube, broadcast_id: str, thumbnail_path: str) -> Dict:
        """Set the thumbnail for a YouTube live broadcast."""
        request = youtube.thumbnails().set(
            videoId=broadcast_id,
            media_body=thumbnail_path
        )
        response = request.execute()
        logger.info(f"Set thumbnail for broadcast: {broadcast_id}")
        return response

    def _create_stream(self, youtube, title: str) -> Dict:
        """Create a YouTube Live stream with RTMP configuration."""
        res = youtube.liveStreams().insert(
            part="snippet,cdn",
            body=dict(
                snippet=dict(
                    title=title
                ),
                cdn=dict(
                    format="720p",
                    ingestionType="rtmp",
                    resolution="720p",
                    frameRate="30fps"
                )
            )
        ).execute()

        logger.info(f"Created stream: {res['id']}")
        return res

    def _bind_broadcast_to_stream(self, youtube, broadcast_id: str, stream_id: str) -> Dict:
        """Bind a broadcast to a stream."""
        bind_response = youtube.liveBroadcasts().bind(
            part="id,contentDetails",
            id=broadcast_id,
            streamId=stream_id
        ).execute()

        logger.info(f"Bound broadcast {broadcast_id} to stream {stream_id}")
        return bind_response

    def stop_live(self, youtube, broadcast_id: str) -> Dict:
        """Stop a live broadcast on YouTube."""
        res = youtube.liveBroadcasts().transition(
            broadcastStatus="complete",
            id=broadcast_id,
            part="id,status"
        ).execute()

        logger.info(f"Stopped broadcast: {broadcast_id}")
        return res
