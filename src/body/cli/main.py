"""Body CLI - REST API Server Entry Point"""
import os
import uvicorn
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.routing import Route
from .tools import speak, change_emotion, get_comments
from .io_adapter import start_input_reader_thread

import logging

# ログ設定：ノイズを減らすためにWARNINGレベルに設定
logging.basicConfig(level=logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def health_check(request: Request) -> JSONResponse:
    """ヘルスチェック用エンドポイント"""
    return JSONResponse({"status": "ok"})


async def speak_api(request: Request) -> JSONResponse:
    """
    発話API
    POST /api/speak
    Body: {"text": "発話内容", "style": "neutral"}
    """
    try:
        body = await request.json()
        text = body.get("text", "")
        style = body.get("style", "neutral")
        speaker_id = body.get("speaker_id")
        result = await speak(text, style, speaker_id=speaker_id)
        return JSONResponse({"status": "ok", "result": result})
    except Exception as e:
        logger.error(f"Error in speak API: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


async def change_emotion_api(request: Request) -> JSONResponse:
    """
    表情変更API
    POST /api/change_emotion
    Body: {"emotion": "happy"}
    """
    try:
        body = await request.json()
        emotion = body.get("emotion", "neutral")
        result = await change_emotion(emotion)
        return JSONResponse({"status": "ok", "result": result})
    except Exception as e:
        logger.error(f"Error in change_emotion API: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


async def get_comments_api(request: Request) -> JSONResponse:
    """
    コメント取得API
    GET /api/comments
    """
    try:
        result = await get_comments()
        # 結果をパースしてリストとして返す
        if result == "No new comments.":
            comments = []
        else:
            comments = result.split("\n") if result else []
        return JSONResponse({"status": "ok", "comments": comments})
    except Exception as e:
        logger.error(f"Error in get_comments API: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


# Starletteアプリケーションを構築
routes = [
    Route("/health", health_check, methods=["GET"]),
    Route("/api/speak", speak_api, methods=["POST"]),
    Route("/api/change_emotion", change_emotion_api, methods=["POST"]),
    Route("/api/comments", get_comments_api, methods=["GET"]),
]

app = Starlette(routes=routes)


if __name__ == "__main__":
    # 環境変数からポートを取得（デフォルトは8000）
    port = int(os.getenv("PORT", "8000"))
    # 標準入力読み取り用のスレッドを開始
    start_input_reader_thread()
    # Uvicornでサーバーを起動
    logger.warning(f"Starting Body CLI REST server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, access_log=False)
