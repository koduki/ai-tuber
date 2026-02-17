"""Body Streamer - REST API Server Entry Point"""
import os
import logging
import uvicorn
from starlette.applications import Starlette
from .service import body_service
from .utils import ensure_youtube_secrets
from .youtube import start_comment_polling
from ..rest import BodyApp

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# BodyApp インスタンスを生成して Starlette app を取得
body_app = BodyApp(body_service)

async def startup():
    """アプリケーション起動時の処理"""
    await body_service.start_worker()

app = Starlette(routes=body_app.get_routes(), on_startup=[startup])


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
