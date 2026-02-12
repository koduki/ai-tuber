"""Body Streamer - REST API Server Entry Point"""
import os
import logging
import uvicorn
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.routing import Route
from .tools import speak, change_emotion, get_comments, start_obs_recording, stop_obs_recording, play_audio_file, start_streaming, stop_streaming, get_streaming_comments
from .utils import ensure_youtube_secrets
from .youtube import start_comment_polling

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
        result = await speak(text, style, speaker_id)
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
        # JSON文字列をパースしてリストとして返す
        import json
        comments = json.loads(result) if result else []
        return JSONResponse({"status": "ok", "comments": comments})
    except Exception as e:
        logger.error(f"Error in get_comments API: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


async def start_recording_api(request: Request) -> JSONResponse:
    """
    OBS録画開始API
    POST /api/recording/start
    """
    try:
        result = await start_obs_recording()
        return JSONResponse({"status": "ok", "result": result})
    except Exception as e:
        logger.error(f"Error in start_recording API: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


async def stop_recording_api(request: Request) -> JSONResponse:
    """
    OBS録画停止API
    POST /api/recording/stop
    """
    try:
        result = await stop_obs_recording()
        return JSONResponse({"status": "ok", "result": result})
    except Exception as e:
        logger.error(f"Error in stop_recording API: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


async def play_audio_file_api(request: Request) -> JSONResponse:
    """
    音声ファイル再生API (完了まで待機)
    POST /api/play_audio_file
    Body: {"file_path": "/app/shared/voice/speech_1234.wav", "duration": 5.2}
    """
    try:
        body = await request.json()
        file_path = body.get("file_path")
        duration = body.get("duration", 0.0)
        
        if not file_path:
            return JSONResponse({"status": "error", "message": "file_path is required"}, status_code=400)
        
        result = await play_audio_file(file_path, duration)
        return JSONResponse({"status": "ok", "result": result})
    except Exception as e:
        logger.error(f"Error in play_audio_file API: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


async def start_streaming_api(request: Request) -> JSONResponse:
    """
    YouTube Live配信開始API
    POST /api/streaming/start
    Body: {
        "title": "配信タイトル",
        "description": "配信説明",
        "scheduled_start_time": "2024-12-31T00:00:00.000Z",
        "thumbnail_path": "/path/to/thumbnail.png",
        "privacy_status": "private"
    }
    """
    try:
        body = await request.json()
        title = body.get("title", "AI Tuber Live Stream")
        description = body.get("description", "")
        scheduled_start_time = body.get("scheduled_start_time")
        thumbnail_path = body.get("thumbnail_path")
        privacy_status = body.get("privacy_status", "private")
        
        if not scheduled_start_time:
            return JSONResponse({"status": "error", "message": "scheduled_start_time is required"}, status_code=400)
        
        result = await start_streaming(title, description, scheduled_start_time, thumbnail_path, privacy_status)
        return JSONResponse({"status": "ok", "result": result})
    except Exception as e:
        logger.error(f"Error in start_streaming API: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


async def stop_streaming_api(request: Request) -> JSONResponse:
    """
    YouTube Live配信停止API
    POST /api/streaming/stop
    """
    try:
        result = await stop_streaming()
        return JSONResponse({"status": "ok", "result": result})
    except Exception as e:
        logger.error(f"Error in stop_streaming API: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


async def get_streaming_comments_api(request: Request) -> JSONResponse:
    """
    YouTube Live配信コメント取得API
    GET /api/streaming/comments
    """
    try:
        result = await get_streaming_comments()
        # JSON文字列をパースしてリストとして返す
        import json
        comments = json.loads(result) if result else []
        return JSONResponse({"status": "ok", "comments": comments})
    except Exception as e:
        logger.error(f"Error in get_streaming_comments API: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


# Starletteアプリケーションを構築
routes = [
    Route("/health", health_check, methods=["GET"]),
    Route("/api/speak", speak_api, methods=["POST"]),
    Route("/api/change_emotion", change_emotion_api, methods=["POST"]),
    Route("/api/play_audio_file", play_audio_file_api, methods=["POST"]),
    Route("/api/comments", get_comments_api, methods=["GET"]),
    Route("/api/recording/start", start_recording_api, methods=["POST"]),
    Route("/api/recording/stop", stop_recording_api, methods=["POST"]),
    Route("/api/streaming/start", start_streaming_api, methods=["POST"]),
    Route("/api/streaming/stop", stop_streaming_api, methods=["POST"]),
    Route("/api/streaming/comments", get_streaming_comments_api, methods=["GET"]),
]

app = Starlette(routes=routes)


if __name__ == "__main__":
    # 環境変数からポートを取得（デフォルトは8000）
    port = int(os.getenv("PORT", "8000"))
    
    # YouTube コメントポーリングを開始
    logger.info("Starting YouTube comment polling...")
    start_comment_polling()
    
    # OBS初期化用のダミーファイル作成
    try:
        voice_dir = "/app/shared/voice"
        os.makedirs(voice_dir, exist_ok=True)
        
        # 起動時に古い音声ファイルをクリーンアップ
        logger.info("Cleaning up old voice files...")
        audio_files_deleted = 0
        for filename in os.listdir(voice_dir):
            if filename.startswith("speech_") and filename.endswith(".wav") and filename != "speech_0000.wav":
                try:
                    file_path = os.path.join(voice_dir, filename)
                    os.remove(file_path)
                    audio_files_deleted += 1
                except Exception as e:
                    logger.warning(f"Failed to delete {filename}: {e}")
        logger.info(f"Cleaned up {audio_files_deleted} old voice files")
        
        # ダミーファイル作成
        dummy_file = os.path.join(voice_dir, "speech_0000.wav")
        if not os.path.exists(dummy_file) or os.path.getsize(dummy_file) == 0:
            # 最小限の無音WAVヘッダ (1秒, モノラル, 44100Hz, 16bit)
            silent_wav = (
                b'RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00'
                b'\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
            )
            with open(dummy_file, "wb") as f:
                f.write(silent_wav)
            logger.info(f"Created valid dummy silent WAV: {dummy_file}")
    except Exception as e:
        logger.warning(f"Failed to create dummy audio file: {e}")
    
    # YouTube秘匿情報を環境変数からファイルに出力 (Docker用)
    ensure_youtube_secrets()

    # Uvicornでサーバーを起動
    logger.info(f"Starting Body Streamer REST server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, access_log=False)
