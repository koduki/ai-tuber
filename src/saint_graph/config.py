from __future__ import annotations

import os
import logging
from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    # NOTE:
    # - docker-compose(local dev) では service DNS として tools-weather が解決できる
    # - Cloud Run では tools-weather は解決できないため、必ず公開URLを env から渡す
    # 優先順位:
    #   1) WEATHER_MCP_URL (推奨: Cloud Run)
    #   2) MCP_URL (後方互換)
    #   3) default (ローカル/dev)
    mcp_url: str = os.getenv(
        "WEATHER_MCP_URL",
        os.getenv("MCP_URL", "http://tools-weather:8001/sse"),
    )

    body_url: str = os.getenv("BODY_URL", "http://localhost:8000")

_config = Config()
MCP_URL = _config.mcp_url
BODY_URL = _config.body_url

# 動作モード
RUN_MODE = os.getenv("RUN_MODE", "cli")

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
