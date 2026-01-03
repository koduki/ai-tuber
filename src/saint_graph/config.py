import os
import logging

# 環境設定
RUN_MODE = os.getenv("RUN_MODE", "cli")
# MCP_URLS can be a comma-separated list
if RUN_MODE == "cli":
    _url_str = os.getenv("MCP_URLS_CLI", "http://mcp-cli:8000/sse")
else:
    _url_str = os.getenv("MCP_URLS_PROD", "")

# カンマ区切りなどが残っていても、先頭の1つだけを採用する、または単純に文字列として扱う
MCP_URL = _url_str.split(",")[0].strip()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = "gemini-2.5-flash-lite" # リクエストされたliteモデルを使用

# 定数
POLL_INTERVAL = 0.5
SOLILOQUY_INTERVAL = 30.0 # 30秒間の沈黙でランダムな発話
HISTORY_LIMIT = 12
NEWS_DIR = os.getenv("NEWS_DIR", "/app/data/news")

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("saint-graph")

# ノイズの多いライブラリを黙らせる
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("mcp_client").setLevel(logging.WARNING)
logging.getLogger("google_adk").setLevel(logging.WARNING)
