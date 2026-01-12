import os
import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse
from .tools import speak, change_emotion, get_comments
from .io_adapter import start_input_reader_thread

import logging

# ログ設定：ノイズを減らすためにWARNINGレベルに設定
logging.basicConfig(level=logging.WARNING)
logging.getLogger("mcp").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

# FastMCPサーバーの初期化
mcp = FastMCP("body-cli")

@mcp.tool(name="speak")
async def speak_tool(text: str, style: str = None) -> str:
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
    # 標準入力読み取り用のスレッドを開始
    start_input_reader_thread()
    # Uvicornでサーバーを起動
    uvicorn.run(app, host="0.0.0.0", port=port, access_log=False)
