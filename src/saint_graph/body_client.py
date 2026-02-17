"""Body REST API Client for saint_graph.

Provides HTTP client for calling body-cli/body-streamer REST APIs.
"""
import httpx
import logging
from typing import Optional, List, Dict, Any

from .config import BODY_URL

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
                      uses the BODY_URL from config.
        """
        self.base_url = (base_url or BODY_URL).rstrip("/")
        logger.info(f"BodyClient initialized with base_url: {self.base_url}")

    async def _request(self, method: str, path: str, payload: Optional[Dict[str, Any]] = None, timeout: float = DEFAULT_TIMEOUT) -> Optional[Dict[str, Any]]:
        """共通のリクエスト処理。"""
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                if method.upper() == "POST":
                    response = await client.post(url, json=payload)
                else:
                    response = await client.get(url)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Error calling {path} API: {e}")
                return None
    
    async def speak(self, text: str, style: Optional[str] = None, speaker_id: Optional[int] = None) -> str:
        """アバターに発話させます。"""
        payload = {"text": text}
        if style:
            payload["style"] = style
        if speaker_id is not None:
            payload["speaker_id"] = speaker_id
        
        data = await self._request("POST", "/api/speak", payload)
        if data:
            return data.get("result", "Speaking completed")
        return "Error: Failed to call speak API"
    
    async def change_emotion(self, emotion: str) -> str:
        """アバターの表情を変更します。"""
        data = await self._request("POST", "/api/change_emotion", {"emotion": emotion})
        if data:
            return data.get("result", f"Emotion changed to {emotion}")
        return f"Error: Failed to change emotion to {emotion}"
    
    async def get_comments(self) -> List[Dict[str, Any]]:
        """直近のユーザーコメントを取得します。"""
        data = await self._request("GET", "/api/comments")
        if data:
            return data.get("comments", [])
        return []
    
    async def start_broadcast(self, config: Optional[Dict[str, Any]] = None) -> str:
        """配信または録画を開始します。"""
        data = await self._request("POST", "/api/broadcast/start", config or {})
        if data:
            return data.get("result", "Broadcast started")
        return "Error: Failed to start broadcast"
    
    async def stop_broadcast(self) -> str:
        """配信または録画を停止します。"""
        data = await self._request("POST", "/api/broadcast/stop")
        if data:
            return data.get("result", "Broadcast stopped")
        return "Error: Failed to stop broadcast"

    async def wait_for_queue(self, timeout: float = 300.0) -> str:
        """キュー内のすべての処理が完了するまで待機します。"""
        data = await self._request("POST", "/api/queue/wait", timeout=timeout)
        if data:
            return data.get("result", "Wait completed")
        return "Error: Failed to wait for queue"

    async def health_check(self) -> bool:
        """Body サービスの稼働状態を確認します。"""
        url = f"{self.base_url}/health"
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(url)
                return response.status_code == 200
            except Exception:
                return False
