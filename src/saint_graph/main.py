import asyncio
import sys

from .config import logger, MCP_URLS, POLL_INTERVAL
from .saint_graph import SaintGraph
from .telemetry import setup_telemetry
from .prompt_loader import PromptLoader
from .news_service import NewsService


async def main():
    """ニュースキャスター配信のメインエントリーポイント。"""
    setup_telemetry()
    logger.info("Starting Saint Graph in Chat Mode...")

    # プロンプトとテンプレートのロード
    loader = PromptLoader(character_name="ren")
    system_instruction = loader.load_system_instruction()
    
    template_names = [
        "intro", "news_reading", "news_finished", "closing",
        "retry_no_tool", "retry_final_response"
    ]
    templates = loader.load_templates(template_names)
    retry_templates = loader.get_retry_templates(templates)

    # ニュースサービスの初期化
    news_path = "/app/data/news/news_script.md"
    news_service = NewsService(news_path)
    try:
        news_service.load_news()
        if not news_service.items:
            logger.warning(f"NewsService loaded 0 items from {news_path}.")
        else:
            logger.info(f"Loaded {len(news_service.items)} news items from {news_path}.")
    except Exception as e:
        logger.error(f"Failed to load news: {e}")

    # SaintGraph (ADK) の初期化
    saint_graph = SaintGraph(
        mcp_urls=MCP_URLS, 
        system_instruction=system_instruction,
        retry_templates=retry_templates
    )

    # メインループ
    await _run_newscaster_loop(saint_graph, news_service, templates)


async def _run_newscaster_loop(saint_graph: SaintGraph, news_service: NewsService, templates: dict):
    """ニュースキャスターのメインループを実行します。"""
    logger.info("Entering Newscaster Loop...")

    finished_news = False
    end_wait_counter = 0
    MAX_WAIT_CYCLES = 20

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
                    await saint_graph.close()
                    break

            await asyncio.sleep(POLL_INTERVAL)

        except Exception as e:
            logger.error(f"Unexpected error in Chat Loop: {e}", exc_info=True)
            await asyncio.sleep(5)
        except BaseException as e:
            logger.critical(f"Critical System Error: {e}", exc_info=True)
            raise


async def _check_comments(saint_graph: SaintGraph) -> bool:
    """コメントをポーリングし、あれば応答します。インタラクションがあればTrueを返します。"""
    try:
        comments = await saint_graph.call_tool("sys_get_comments", {})
        if comments and comments != "No new comments.":
            logger.info(f"Comments received: {comments}")
            await saint_graph.process_turn(comments)
            return True
    except Exception as e:
        if "not found in any toolset" in str(e):
            logger.warning("Waiting for sys_get_comments tool to become available...")
        else:
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
