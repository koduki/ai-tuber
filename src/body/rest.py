"""
Body Service REST API Base Class.
Ensures consistent REST interface across different body implementations.
"""
import logging
import json
from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.routing import Route
from .service import BodyServiceBase

logger = logging.getLogger(__name__)

class BodyApp:
    """
    Body サービスの REST API を管理する基底クラス。
    """

    def __init__(self, service: BodyServiceBase):
        self.service = service

    async def health_check(self, request: Request) -> JSONResponse:
        return JSONResponse({"status": "ok"})

    async def speak_api(self, request: Request) -> JSONResponse:
        try:
            body = await request.json()
            text = body.get("text", "")
            style = body.get("style", "neutral")
            speaker_id = body.get("speaker_id")
            result = await self.service.speak(text, style, speaker_id)
            return JSONResponse({"status": "ok", "result": result})
        except Exception as e:
            logger.error(f"Error in speak API: {e}")
            return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

    async def change_emotion_api(self, request: Request) -> JSONResponse:
        try:
            body = await request.json()
            emotion = body.get("emotion", "neutral")
            result = await self.service.change_emotion(emotion)
            return JSONResponse({"status": "ok", "result": result})
        except Exception as e:
            logger.error(f"Error in change_emotion API: {e}")
            return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

    async def get_comments_api(self, request: Request) -> JSONResponse:
        try:
            result = await self.service.get_comments()
            comments = json.loads(result) if result else []
            return JSONResponse({"status": "ok", "comments": comments})
        except Exception as e:
            logger.error(f"Error in get_comments API: {e}")
            return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

    async def start_broadcast_api(self, request: Request) -> JSONResponse:
        try:
            body = await request.json() if request.headers.get("content-type") == "application/json" else {}
            result = await self.service.start_broadcast(body)
            return JSONResponse({"status": "ok", "result": result})
        except Exception as e:
            logger.error(f"Error in start_broadcast API: {e}")
            return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

    async def stop_broadcast_api(self, request: Request) -> JSONResponse:
        try:
            result = await self.service.stop_broadcast()
            return JSONResponse({"status": "ok", "result": result})
        except Exception as e:
            logger.error(f"Error in stop_broadcast API: {e}")
            return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

    async def wait_for_queue_api(self, request: Request) -> JSONResponse:
        try:
            result = await self.service.wait_for_queue()
            return JSONResponse({"status": "ok", "result": result})
        except Exception as e:
            logger.error(f"Error in wait_for_queue API: {e}")
            return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

    def get_routes(self) -> list[Route]:
        """共通のルート定義を返します。"""
        return [
            Route("/health", self.health_check, methods=["GET"]),
            Route("/api/speak", self.speak_api, methods=["POST"]),
            Route("/api/change_emotion", self.change_emotion_api, methods=["POST"]),
            Route("/api/comments", self.get_comments_api, methods=["GET"]),
            Route("/api/broadcast/start", self.start_broadcast_api, methods=["POST"]),
            Route("/api/broadcast/stop", self.stop_broadcast_api, methods=["POST"]),
            Route("/api/queue/wait", self.wait_for_queue_api, methods=["POST"]),
        ]
