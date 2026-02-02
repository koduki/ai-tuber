"""Body REST API Client for saint_graph.

Provides HTTP client for calling body-cli/body-streamer REST APIs.
"""
import httpx
import logging
from typing import Optional, List, Dict, Any

from .config import MCP_URLS

logger = logging.getLogger(__name__)

# Default timeout for HTTP requests
DEFAULT_TIMEOUT = 30.0


class BodyClient:
    """REST API client for body services (CLI/Streamer)."""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize the body client.
        
        Args:
            base_url: Base URL for the body service. If not provided,
                      uses the first URL from MCP_URLS (converted to REST format).
        """
        if base_url:
            self.base_url = base_url.rstrip("/")
        else:
            # Convert MCP URL (http://body-cli:8000/sse) to REST base URL
            mcp_url = MCP_URLS[0] if MCP_URLS else "http://body-cli:8000/sse"
            self.base_url = mcp_url.replace("/sse", "")
        
        logger.info(f"BodyClient initialized with base_url: {self.base_url}")
    
    async def speak(self, text: str, style: Optional[str] = None, speaker_id: Optional[int] = None) -> str:
        """
        Call the speak API.
        
        Args:
            text: Text to speak
            style: Optional speaking style
            speaker_id: Optional local speaker_id override
            
        Returns:
            Result message from the API
        """
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            try:
                payload = {"text": text}
                if style:
                    payload["style"] = style
                if speaker_id is not None:
                    payload["speaker_id"] = speaker_id
                
                response = await client.post(
                    f"{self.base_url}/api/speak",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                return data.get("result", "Speaking completed")
            except Exception as e:
                logger.error(f"Error calling speak API: {e}")
                return f"Error: {e}"
    
    async def change_emotion(self, emotion: str) -> str:
        """
        Call the change_emotion API.
        
        Args:
            emotion: Emotion to change to (neutral, happy, sad, angry, etc.)
            
        Returns:
            Result message from the API
        """
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/change_emotion",
                    json={"emotion": emotion}
                )
                response.raise_for_status()
                data = response.json()
                return data.get("result", f"Emotion changed to {emotion}")
            except Exception as e:
                logger.error(f"Error calling change_emotion API: {e}")
                return f"Error: {e}"
    
    async def get_comments(self) -> List[Dict[str, Any]]:
        """
        Call the get_comments API.
        
        Returns:
            List of comments (may be empty)
        """
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            try:
                response = await client.get(f"{self.base_url}/api/comments")
                response.raise_for_status()
                data = response.json()
                return data.get("comments", [])
            except Exception as e:
                logger.error(f"Error calling get_comments API: {e}")
                return []
    
    async def start_recording(self) -> str:
        """
        Call the start_recording API (streamer only).
        
        Returns:
            Result message from the API
        """
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            try:
                response = await client.post(f"{self.base_url}/api/recording/start")
                response.raise_for_status()
                data = response.json()
                return data.get("result", "Recording started")
            except Exception as e:
                logger.error(f"Error calling start_recording API: {e}")
                return f"Error: {e}"
    
    async def stop_recording(self) -> str:
        """
        Call the stop_recording API (streamer only).
        
        Returns:
            Result message from the API
        """
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            try:
                response = await client.post(f"{self.base_url}/api/recording/stop")
                response.raise_for_status()
                data = response.json()
                return data.get("result", "Recording stopped")
            except Exception as e:
                logger.error(f"Error calling stop_recording API: {e}")
                return f"Error: {e}"
    
    async def play_audio_file(self, file_path: str, duration: float) -> str:
        """
        Call the play_audio_file API (plays pre-generated audio and waits for completion).
        
        Args:
            file_path: Path to the audio file
            duration: Duration of the audio in seconds
            
        Returns:
            Result message from the API
        """
        async with httpx.AsyncClient(timeout=duration + 10.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/play_audio_file",
                    json={"file_path": file_path, "duration": duration}
                )
                response.raise_for_status()
                data = response.json()
                return data.get("result", "Playback completed")
            except Exception as e:
                logger.error(f"Error calling play_audio_file API: {e}")
                return f"Error: {e}"
    
    async def health_check(self) -> bool:
        """
        Check if the body service is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
            except Exception:
                return False
