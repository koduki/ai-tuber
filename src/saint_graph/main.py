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

    try:
        # 配信パラメータの構築 & 配信開始
        broadcast_config = _build_broadcast_config()
        await _start_broadcast(body_client, broadcast_config)

        # 配信開始後、OBSの映像ソース（GPUデコーダー）が安定するまで待機
        # この間は OBS は RTMP を push しているが YouTube Live はまだ視聴者に非公開 (testing)
        # BROADCAST_START_DELAY を調整することで冒頭のブラックアウト期間を回避できる
        # ★ 同時に intro の LLM 推論を先行実行しておく（go_live 直後に即発話するため）
        start_delay = float(os.getenv("BROADCAST_START_DELAY", "90"))
        logger.info(f"Waiting {start_delay}s for OBS to stabilize. Pre-computing intro in parallel...")
        precompute_task = asyncio.create_task(saint_graph.precompute_intro())
        await asyncio.sleep(start_delay)
        if not precompute_task.done():
            logger.info("Intro pre-computation still running, waiting for it to finish...")
            await precompute_task
        logger.info("OBS stabilization wait complete. Intro pre-computation done. Going live...")

        # Phase 2: YouTube Live を視聴者に公開（testing -> live）
        # イントロは precompute 済みなので go_live の直後にすぐ発話できる
        await _go_live(body_client)

        # ステートマシンによるメインループ実行
        ctx = BroadcastContext(
            saint_graph=saint_graph,
            news_service=news_service,
        )

        await run_broadcast_loop(ctx)
    finally:
        await _stop_broadcast(body_client)
        await saint_graph.close()


def _build_broadcast_config() -> dict:
    """環境変数から配信パラメータを構築します。"""
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    now_iso = now.strftime('%Y-%m-%dT%H:%M:%SZ')
    # YouTube Live API は scheduledStartTime が現在時刻と同一か過去の場合に
    # epoch (1970年) として表示されることがある。
    # 実際の go_live() は BROADCAST_START_DELAY 後に呼ぶため、
    # scheduled はそれより十分先の未来を指定する。
    scheduled_start = now + timedelta(minutes=5)
    scheduled_start_iso = scheduled_start.strftime('%Y-%m-%dT%H:%M:%SZ')
    return {
        "title": os.getenv("STREAM_TITLE", f"AI Tuber Live Stream - {now_iso}"),
        "description": os.getenv("STREAM_DESCRIPTION", "AI Tuber Live Stream"),
        "scheduled_start_time": scheduled_start_iso,
        "privacy_status": os.getenv("STREAM_PRIVACY", "private"),
    }


async def _start_broadcast(body: BodyClient, config: dict):
    """配信または録画を開始します（OBSウォームアップ）。"""
    try:
        res = await body.start_broadcast(config)
        logger.info(f"Broadcast start result: {res}")
        if "エラー" in res or res.startswith("Error"):
            raise RuntimeError(f"Broadcast start failed: {res}")
    except Exception as e:
        logger.critical(f"Could not start broadcast: {e}")
        raise


async def _go_live(body: BodyClient):
    """YouTube Live を視聴者に公開します (testing -> live)。"""
    try:
        res = await body.go_live()
        logger.info(f"Go live result: {res}")
    except Exception as e:
        logger.warning(f"go_live failed (non-fatal): {e}")


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
