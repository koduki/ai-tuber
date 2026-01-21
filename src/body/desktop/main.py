"""Body Desktop - MCP Server Entry Point"""
import os
import logging
import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse
from .tools import speak, change_emotion, get_comments
from .youtube import start_comment_polling

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.getLogger("mcp").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# FastMCPサーバーの初期化
mcp = FastMCP("body-desktop")


@mcp.tool(name="speak")
async def speak_tool(text: str, style: str = "normal") -> str:
    """視聴者に対してテキストを発話します。"""
    return await speak(text, style)


@mcp.tool(name="change_emotion")
async def change_emotion_tool(emotion: str) -> str:
    """アバターの表情（感情）を変更します。"""
    return await change_emotion(emotion)


@mcp.tool(name="sys_get_comments")
async def sys_get_comments() -> str:
    """
    ユーザーからのコメントを取得します。
    システム内部用ツールとして設計されており、エージェントによる直接呼び出しは想定していません。
    """
    return await get_comments()


# Dockerネットワーク内でのDNSリバインディング保護を無効化
mcp.settings.transport_security.enable_dns_rebinding_protection = False


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    """ヘルスチェック用エンドポイント"""
    return JSONResponse({"status": "ok"})


# FastMCPからStarlette（ASGI）アプリを取得
app = mcp.sse_app()


if __name__ == "__main__":
    # 環境変数からポートを取得（デフォルトは8000）
    port = int(os.getenv("PORT", "8000"))
    
    # YouTube コメントポーリングを開始
    logger.info("Starting YouTube comment polling...")
    start_comment_polling()
    
    # OBS初期化用のダミーファイル作成
    try:
        os.makedirs("/app/shared/audio", exist_ok=True)
        dummy_file = os.path.join("/app/shared/audio", "speech_0000.wav")
        if not os.path.exists(dummy_file) or os.path.getsize(dummy_file) == 0:
            # 最小限の無音WAVヘッダ (1秒, モノラル, 44100Hz, 16bit)
            # RIFFヘッダ + fmtチャンク + dataチャンク
            silent_wav = (
                b'RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00'
                b'\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
            )
            with open(dummy_file, "wb") as f:
                f.write(silent_wav)
            logger.info(f"Created valid dummy silent WAV: {dummy_file}")
    except Exception as e:
        logger.warning(f"Failed to create dummy audio file: {e}")
    
    # Uvicornでサーバーを起動
    logger.info(f"Starting Body Desktop MCP server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, access_log=False)
