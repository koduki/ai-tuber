from __future__ import annotations

import os
import logging
import sys
from dataclasses import dataclass, fields, field
from typing import Optional
from src.saas.secret_provider import SecretProvider, create_secret_provider

# ログ設定（初期化）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("saint-graph")

@dataclass(frozen=True)
class Config:
    # 優先順位:
    #   1) WEATHER_MCP_URL (推奨: Cloud Run)
    #   2) MCP_URL (非推奨)
    #   3) default (ローカル/dev)
    mcp_url: str = field(default_factory=lambda: os.getenv("WEATHER_MCP_URL") or os.getenv("MCP_URL") or "http://tools-weather:8001/sse")
    body_url: str = field(default_factory=lambda: os.getenv("BODY_URL") or "http://localhost:8000")
    
    # AI設定
    google_api_key: str | None = None  # SecretProvider 経由で取得（後で設定）
    model_name: str = field(default_factory=lambda: os.getenv("MODEL_NAME", "gemini-2.5-flash-lite"))
    adk_telemetry: bool = field(default_factory=lambda: os.getenv("ADK_TELEMETRY", "false").lower() == "true")
    
    # システム定数
    poll_interval: float = 1.0
    news_dir: str = field(default_factory=lambda: os.getenv("NEWS_DIR", "/app/data/news"))
    max_wait_cycles: int = field(default_factory=lambda: int(os.getenv("MAX_WAIT_CYCLES", "30")))
    
    # Cloud Run判定
    is_cloud_run: bool = field(default_factory=lambda: os.getenv("K_SERVICE") is not None or os.getenv("CLOUD_RUN_JOB") is not None)

    def validate(self):
        """設定の妥当性を検証します。"""
        # Cloud Run 環境での必須チェック
        if self.is_cloud_run:
            if not os.getenv("WEATHER_MCP_URL"):
                logger.error("CRITICAL: WEATHER_MCP_URL is not set in Cloud Run environment!")
                sys.exit(1)
        
        # 非推奨の環境変数警告
        if os.getenv("MCP_URL") and not os.getenv("WEATHER_MCP_URL"):
            logger.warning("DEPRECATED: MCP_URL is deprecated. Please use WEATHER_MCP_URL instead.")

    def log_config(self):
        """安全な範囲で設定をログ出力します。"""
        logger.info("Initializing Saint Graph Config...")
        mask_keys = {"google_api_key"}
        for field in fields(self):
            value = getattr(self, field.name)
            if field.name in mask_keys:
                log_value = "********" if value else "None"
            else:
                log_value = value
            logger.info(f"Config: {field.name} = {log_value}")


def _load_google_api_key(secret_provider: Optional[SecretProvider] = None) -> str | None:
    """
    SecretProvider を使って GOOGLE_API_KEY を取得。
    フォールバック: 環境変数から直接読む（互換性のため）
    """
    if secret_provider is None:
        secret_provider = create_secret_provider()
    
    try:
        return secret_provider.get_secret("GOOGLE_API_KEY")
    except (ValueError, FileNotFoundError):
        # SecretProvider で取得できない場合は環境変数をフォールバック
        logger.warning("Failed to load GOOGLE_API_KEY from SecretProvider, falling back to env var")
        return os.getenv("GOOGLE_API_KEY")


_config_base = Config()
_config_base.validate()

# google_api_key を SecretProvider 経由で取得
_google_api_key = _load_google_api_key()

# 新しい Config インスタンスを作成（frozen なので再作成）
_config = Config(
    mcp_url=_config_base.mcp_url,
    body_url=_config_base.body_url,
    google_api_key=_google_api_key,
    model_name=_config_base.model_name,
    adk_telemetry=_config_base.adk_telemetry,
    poll_interval=_config_base.poll_interval,
    news_dir=_config_base.news_dir,
    max_wait_cycles=_config_base.max_wait_cycles,
    is_cloud_run=_config_base.is_cloud_run
)

_config.log_config()

# 既存コードとの互換性のための定数
MCP_URL = _config.mcp_url
BODY_URL = _config.body_url
GOOGLE_API_KEY = _config.google_api_key
MODEL_NAME = _config.model_name
ADK_TELEMETRY = _config.adk_telemetry
POLL_INTERVAL = _config.poll_interval
NEWS_DIR = _config.news_dir
MAX_WAIT_CYCLES = _config.max_wait_cycles

# 動作モード
RUN_MODE = os.getenv("RUN_MODE", "cli")

# 外部ライブラリのログ抑制
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("mcp").setLevel(logging.INFO)
logging.getLogger("google_adk").setLevel(logging.INFO)
logging.getLogger("google_genai").setLevel(logging.WARNING)
