import asyncio
import sys
import os

from .config import logger, BODY_URL, MCP_URLS, POLL_INTERVAL, MAX_WAIT_CYCLES, NEWS_DIR
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

    # SaintGraph (ADK + REST Body) の初期化
    saint_graph = SaintGraph(
        body_url=BODY_URL,
        mcp_urls=MCP_URLS, 
        system_instruction=system_instruction,
        mind_config=mind_config
    )

    # メインループ
    await _run_newscaster_loop(saint_graph, news_service, templates)


async def _run_newscaster_loop(saint_graph: SaintGraph, news_service: NewsService, templates: dict):
    """ニュースキャスターのメインループを実行します。"""
    logger.info("Entering Newscaster Loop...")

    finished_news = False
    end_wait_counter = 0

    # 録画開始の試行 (REST API)
    try:
        res = await saint_graph.body.start_recording()
        logger.info(f"Automatic Recording Start result: {res}")
    except Exception as e:
        logger.warning(f"Could not automatically start recording: {e}")

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
                    
                    # 録画停止の試行
                    try:
                        await saint_graph.body.stop_recording()
                    except:
                        pass
                        
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
        # BodyClient経由でコメント取得 (REST API)
        comments_data = await saint_graph.body.get_comments()
        
        if comments_data:
            # コメントの整形（リストから文字列へ）
            if isinstance(comments_data, list):
                # body-streamerの場合の形式
                if comments_data and isinstance(comments_data[0], dict):
                    comments_text = "\n".join([f"{c['author']}: {c['message']}" for c in comments_data])
                else:
                    # body-cliの場合の形式
                    comments_text = "\n".join(comments_data)
            else:
                comments_text = str(comments_data)
                
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
