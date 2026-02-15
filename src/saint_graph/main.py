import asyncio
import sys
import os

from .config import logger, BODY_URL, MCP_URL, POLL_INTERVAL, MAX_WAIT_CYCLES, NEWS_DIR
from .saint_graph import SaintGraph
from .telemetry import setup_telemetry
from .prompt_loader import PromptLoader
from .news_service import NewsService
from .body_client import BodyClient


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
        mcp_url=MCP_URL,
        system_instruction=system_instruction,
        mind_config=mind_config
    )

    # MCP URL の疎通確認（デバッグ用）
    if MCP_URL:
        import httpx
        logger.info(f"Checking connectivity to MCP_URL: {MCP_URL}")
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # SSEなのでGETはぶら下がる可能性があるが、まずは疎通を見たいので5秒で切る前提
                response = await client.get(MCP_URL)
                logger.info(f"MCP_URL check response: {response.status_code}")
        except asyncio.TimeoutError:
            logger.info("MCP_URL check: connection timed out as expected (SSE)")
        except Exception as e:
            logger.warning(f"MCP_URL connectivity check failed: {e}")

    # メインループ
    await _run_newscaster_loop(saint_graph, news_service, templates)


async def _run_newscaster_loop(saint_graph: SaintGraph, news_service: NewsService, templates: dict):
    """ニュースキャスターのメインループを実行します。"""
    logger.info("Entering Newscaster Loop...")

    finished_news = False
    end_wait_counter = 0

    # 配信パラメータの構築
    broadcast_config = _build_broadcast_config()

    # 録画・配信開始
    await _start_broadcast(saint_graph.body, broadcast_config)

    # 配信開始の挨拶
    await saint_graph.process_turn(templates["intro"], context="Intro")

    while True:
        try:
            # ユーザーからのコメント確認
            has_user_interaction = await _check_comments(saint_graph)
            if has_user_interaction:
                end_wait_counter = 0
                await asyncio.sleep(POLL_INTERVAL)
                continue

            # ニュース読み上げまたは終了処理
            if news_service.has_next():
                item = news_service.get_next_item()
                logger.info(f"Reading news item: {item.title}")
                instruction = templates["news_reading"].format(title=item.title, content=item.content)
                await saint_graph.process_turn(instruction, context=f"News Reading: {item.title}")
            elif not finished_news:
                finished_news = True
                logger.info("All news items read. Waiting for final comments.")
                await saint_graph.process_turn(templates["news_finished"], context="News Finished")
            else:
                end_wait_counter += 1
                if end_wait_counter > MAX_WAIT_CYCLES:
                    logger.info(f"Silence timeout ({MAX_WAIT_CYCLES}s) reached. Finishing broadcast.")
                    await saint_graph.process_turn(templates["closing"], context="Closing")
                    await asyncio.sleep(3)
                    
                    await _stop_broadcast(saint_graph.body)
                        
                    await saint_graph.close()
                    break

            await asyncio.sleep(POLL_INTERVAL)

        except Exception as e:
            logger.error(f"Unexpected error in Chat Loop: {e}", exc_info=True)
            await asyncio.sleep(5)
        except BaseException as e:
            logger.critical(f"Critical System Error: {e}", exc_info=True)
            raise


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


async def _check_comments(saint_graph: SaintGraph) -> bool:
    """コメントをポーリングし、あれば応答します。インタラクションがあればTrueを返します。"""
    try:
        comments_data = await saint_graph.body.get_comments()
        
        if comments_data:
            # 共通の形式（List[Dict[str, str]]）で処理
            comments_text = "\n".join([f"{c.get('author', 'User')}: {c.get('message', '')}" for c in comments_data])
            if comments_text:
                logger.info(f"Comments received: {comments_text}")
                await saint_graph.process_turn(comments_text)
                return True
    except Exception as e:
        logger.error(f"Error in polling/turn: {e}")
    return False


if __name__ == "__main__":
    import traceback
    try:
        asyncio.run(main())
    except Exception:
        traceback.print_exc()
        sys.stderr.flush()
        sys.stdout.flush()
        sys.stdout.flush()
