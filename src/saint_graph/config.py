import os
import logging

# 動作モード
RUN_MODE = os.getenv("RUN_MODE", "cli")

# Body (REST API) のベースURL
# Docker環境でのデフォルトを設定
if RUN_MODE == "cli":
    BODY_URL = os.getenv("BODY_URL", "http://body-cli:8000")
else:
    BODY_URL = os.getenv("BODY_URL", "http://body-streamer:8000")

# 外部ツール (MCP) のURL
MCP_URL = os.getenv("MCP_URL", "http://tools-weather:8001/sse")

# AI設定
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.5-flash-lite")
ADK_TELEMETRY = os.getenv("ADK_TELEMETRY", "false").lower() == "true"

# システム定数
POLL_INTERVAL = 1.0        # コメント取得間隔
NEWS_DIR = os.getenv("NEWS_DIR", "/app/data/news")
MAX_WAIT_CYCLES = int(os.getenv("MAX_WAIT_CYCLES", "30")) # 終了までの沈黙カウント(秒)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("saint-graph")

# 外部ライブラリのログ抑制
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("mcp").setLevel(logging.INFO)
logging.getLogger("google_adk").setLevel(logging.INFO)
logging.getLogger("google_genai").setLevel(logging.WARNING)
