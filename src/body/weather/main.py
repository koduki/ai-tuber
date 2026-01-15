import os
import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse
from .tools import get_weather

import logging

# ログ設定：主要な警告のみを出力
logging.basicConfig(level=logging.WARNING)
logging.getLogger("mcp").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

# FastMCPサーバーの初期化
mcp = FastMCP("body-weather")

@mcp.tool(name="get_weather")
async def weather_tool(location: str, date: str = None) -> str:
    """
    指定された場所と日付の天気情報を取得します。
    location: 都市名や地域名（例：東京, 福岡, Tokyo）
    date: 日付 (YYYY-MM-DD) または相対的な指定（today, tomorrow）。未指定時は現在の天気を取得。
    """
    return await get_weather(location, date)

# Dockerネットワーク内での接続エラー回避設定
mcp.settings.transport_security.enable_dns_rebinding_protection = False

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    """ヘルスチェック用エンドポイント"""
    return JSONResponse({"status": "ok"})

# FastMCPからSSE（Server-Sent Events）対応のアプリを取得
app = mcp.sse_app()

if __name__ == "__main__":
    # 環境変数からポートを取得（デフォルトは8001）
    port = int(os.getenv("PORT", "8001"))
    # Uvicornでサーバーを起動
    uvicorn.run(app, host="0.0.0.0", port=port, access_log=False)
