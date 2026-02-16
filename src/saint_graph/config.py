from __future__ import annotations

import os
import logging
import sys
from dataclasses import dataclass, fields, field
from typing import Optional
from infra.secret_provider import SecretProvider, create_secret_provider

# ログ設定（初期化）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("saint-graph")

@dataclass(frozen=True)
class Config:
    """エージェントの設定を管理するクラス。"""
    
    # 接続設定
    weather_mcp_url: str = field(default_factory=lambda: os.getenv("WEATHER_MCP_URL", "http://tools-weather:8001/sse"))
    body_url: str = field(default_factory=lambda: os.getenv("BODY_URL", "http://localhost:8000"))
    
    # AI設定
    google_api_key: str | None = None
    model_name: str = field(default_factory=lambda: os.getenv("MODEL_NAME", "gemini-2.5-flash-lite"))
    adk_telemetry: bool = field(default_factory=lambda: os.getenv("ADK_TELEMETRY", "false").lower() == "true")
    
    # システム定数
    poll_interval: float = field(default_factory=lambda: float(os.getenv("POLL_INTERVAL", "1.0")))
    news_dir: str = field(default_factory=lambda: os.getenv("NEWS_DIR", "news"))
    max_wait_cycles: int = field(default_factory=lambda: int(os.getenv("MAX_WAIT_CYCLES", "30")))
    
    # 動作モード
    run_mode: str = field(default_factory=lambda: os.getenv("RUN_MODE", "cli"))
    is_cloud_run: bool = field(default_factory=lambda: os.getenv("K_SERVICE") is not None or os.getenv("CLOUD_RUN_JOB") is not None)

    def validate(self):
        """設定の妥当性を検証します。"""
        # Cloud Run 環境での必須チェック
        if self.is_cloud_run:
            if not os.getenv("WEATHER_MCP_URL"):
                # ニュース収集ジョブなど、MCPを必要としない場合もあるため、警告に留める
                logger.warning("WEATHER_MCP_URL is not set in Cloud Run environment. MCP features will be disabled.")
        
        if not self.google_api_key:
            logger.error("CRITICAL: GOOGLE_API_KEY is not set. The application cannot function.")
            sys.exit(1)

    def log_config(self):
        """安全な範囲で設定をログ出力します。"""
        logger.info("Initializing Saint Graph Config...")
        mask_keys = {"google_api_key"}
        for f in fields(self):
            value = getattr(self, f.name)
            if f.name in mask_keys:
                log_value = "********" if value else "None"
            else:
                log_value = value
            logger.info(f"Config: {f.name} = {log_value}")


def _load_google_api_key() -> str | None:
    """SecretProvider を使って GOOGLE_API_KEY を取得。"""
    secret_provider = create_secret_provider()
    try:
        return secret_provider.get_secret("GOOGLE_API_KEY")
    except (ValueError, FileNotFoundError):
        logger.warning("Failed to load GOOGLE_API_KEY from SecretProvider, falling back to env var")
        return os.getenv("GOOGLE_API_KEY")


# 設定の初期化
_google_api_key = _load_google_api_key()

# ADK のための環境変数同期
if _google_api_key and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = _google_api_key

_config = Config(google_api_key=_google_api_key)
_config.validate()
_config.log_config()

# モジュールレベルの定数（互換性維持）
WEATHER_MCP_URL = _config.weather_mcp_url
BODY_URL = _config.body_url
GOOGLE_API_KEY = _config.google_api_key
MODEL_NAME = _config.model_name
ADK_TELEMETRY = _config.adk_telemetry
POLL_INTERVAL = _config.poll_interval
NEWS_DIR = _config.news_dir
MAX_WAIT_CYCLES = _config.max_wait_cycles
RUN_MODE = _config.run_mode

# 外部ライブラリのログ抑制
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("mcp").setLevel(logging.INFO)
logging.getLogger("google_adk").setLevel(logging.INFO)
logging.getLogger("google_genai").setLevel(logging.WARNING)
