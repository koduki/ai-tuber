"""YouTube Live API adapter for creating and managing live streams"""
import os
import json
import logging
from typing import Dict, Optional
from body.streamer.youtube_auth import YouTubeAuth

logger = logging.getLogger(__name__)

# YouTube OAuth configuration from environment
YOUTUBE_CLIENT_SECRET_PATH = os.getenv("YOUTUBE_CLIENT_SECRET_PATH", "/secret/google_client_secret.json")
YOUTUBE_TOKEN_PATH = os.getenv("YOUTUBE_TOKEN_PATH", "/secret/yt_token.json")


class YoutubeLiveAdapter:
    """Adapter for YouTube Live API operations"""
    
    def __init__(self) -> None:
        self.youtube, self.creds = self.authenticate_youtube()

    def authenticate_youtube(self):
        """Authenticate to the YouTube API and return the API client."""
        try:
            creds = YouTubeAuth.get_credentials()
            
            # If creds are valid (or were successfully refreshed), build service
            if creds and creds.valid:
                service = YouTubeAuth.get_service(creds)
                return service, creds
            
            # If we reach here, we either have no creds or they are invalid/expired
            # Attempt interactive flow
            logger.info("No valid credentials found. Starting interactive OAuth flow...")
            return YouTubeAuth.start_oauth_flow()
            
        except Exception as e:
            logger.error(f"YouTube authentication failed: {e}")
            raise


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
