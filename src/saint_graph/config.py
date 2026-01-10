import os
import logging

# 環境設定
RUN_MODE = os.getenv("RUN_MODE", "cli")

# MCP connection URL (Single Connection)
if RUN_MODE == "cli":
    MCP_URL = os.getenv("MCP_URL", "http://body-cli:8000/sse")
else:
    MCP_URL = os.getenv("MCP_URL", "")

WEATHER_MCP_URL = os.getenv("WEATHER_MCP_URL", "")
MCP_URLS = [url for url in [MCP_URL, WEATHER_MCP_URL] if url]

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.5-flash-lite")

# 定数
POLL_INTERVAL = 1.0
SOLILOQUY_INTERVAL = 30.0 # 30秒間の沈黙でランダムな発話
HISTORY_LIMIT = 20
NEWS_DIR = os.getenv("NEWS_DIR", "/app/data/news")

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("saint-graph")

# ノイズの多いライブラリを黙らせる
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("mcp").setLevel(logging.WARNING)
logging.getLogger("google_adk").setLevel(logging.WARNING)
