import asyncio
import sys
import os

from .config import logger, BODY_URL, WEATHER_MCP_URL, NEWS_DIR
from .saint_graph import SaintGraph
from .telemetry import setup_telemetry
from .prompt_loader import PromptLoader
from .news_service import NewsService
from .body_client import BodyClient
from .broadcast_loop import BroadcastContext, run_broadcast_loop


async def main():
    """ニュースキャスター配信のメインエントリーポイント。"""
    setup_telemetry()
    logger.info("Starting Saint Graph in Chat Mode...")

    # プロンプトとテンプレートのロード
    loader = PromptLoader(character_name="ren")
    system_instruction = loader.load_system_instruction()
    
    template_names = [
        "intro", "news_reading", "news_finished", "closing"
    ]
    templates = loader.load_templates(template_names)

    # ニュースサービスの初期化
    news_path = os.path.join(NEWS_DIR, "news_script.md")
    news_service = NewsService(news_path)
    try:
        news_service.load_news()
        if not news_service.items:
            logger.warning(f"NewsService loaded 0 items from {news_path}.")
        else:
            logger.info(f"Loaded {len(news_service.items)} news items from {news_path}.")
    except Exception as e:
        logger.error(f"Failed to load news: {e}")

    # キャラクター設定のロード
    mind_config = loader.load_mind_config()
    logger.info(f"Loaded mind config: {mind_config}")

    # BodyClient の初期化
    body_client = BodyClient(base_url=BODY_URL)

    # SaintGraph (ADK + REST Body) の初期化
    saint_graph = SaintGraph(
        body=body_client,
        weather_mcp_url=WEATHER_MCP_URL,
        system_instruction=system_instruction,
        mind_config=mind_config,
        templates=templates
    )

    # MCP URL の疎通確認（デバッグ用）
    if WEATHER_MCP_URL:
        import httpx
        logger.info(f"Checking connectivity to WEATHER_MCP_URL: {WEATHER_MCP_URL}")
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(WEATHER_MCP_URL)
                logger.info(f"WEATHER_MCP_URL check response: {response.status_code}")
        except asyncio.TimeoutError:
            logger.info("WEATHER_MCP_URL check: connection timed out as expected (SSE)")
        except Exception as e:
            logger.warning(f"WEATHER_MCP_URL connectivity check failed: {e}")

    # 配信パラメータの構築 & 配信開始
    broadcast_config = _build_broadcast_config()
    await _start_broadcast(body_client, broadcast_config)

    # ステートマシンによるメインループ実行
    ctx = BroadcastContext(
        saint_graph=saint_graph,
        news_service=news_service,
    )

    try:
        await run_broadcast_loop(ctx)
    finally:
        await _stop_broadcast(body_client)
        await saint_graph.close()


def _build_broadcast_config() -> dict:
    """環境変数から配信パラメータを構築します。"""
    from datetime import datetime
    now_iso = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    return {
        "title": os.getenv("STREAM_TITLE", f"AI Tuber Live Stream - {now_iso}"),
        "description": os.getenv("STREAM_DESCRIPTION", "AI Tuber Live Stream"),
        "scheduled_start_time": now_iso,
        "privacy_status": os.getenv("STREAM_PRIVACY", "private"),
    }


async def _start_broadcast(body: BodyClient, config: dict):
    """配信または録画を開始します。"""
    try:
        res = await body.start_broadcast(config)
        logger.info(f"Broadcast start result: {res}")
        if "エラー" in res or res.startswith("Error"):
            logger.critical(f"Broadcast start failed: {res}")
            sys.exit(1)
    except Exception as e:
        if isinstance(e, SystemExit):
            raise
        logger.critical(f"Could not start broadcast: {e}")
        sys.exit(1)


async def _stop_broadcast(body: BodyClient):
    """配信または録画を停止します。"""
    try:
        res = await body.stop_broadcast()
        logger.info(f"Broadcast stop result: {res}")
    except Exception as e:
        logger.warning(f"Failed to stop broadcast cleanly: {e}")


if __name__ == "__main__":
    import traceback
    try:
        asyncio.run(main())
    except Exception:
        traceback.print_exc()
        sys.stderr.flush()
        sys.stdout.flush()
