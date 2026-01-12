import asyncio
import sys
import os

# 設定とコンポーネントのインポート
from .config import logger, MCP_URLS, POLL_INTERVAL
from .saint_graph import SaintGraph
from .telemetry import setup_telemetry

def load_persona(name: str = "ren") -> str:
    """
    指定されたキャラクターのpersona.mdを読み込み、共通のcore_instructions.mdと結合します。
    """
    base_dir = "/app/src"
    
    # ファイルパスの定義
    core_path = os.path.join(base_dir, "saint_graph", "system_prompts", "core_instructions.md")
    persona_path = os.path.join(base_dir, "mind", name, "persona.md")

    # 共通指示の読み込み
    with open(core_path, "r", encoding="utf-8") as f:
        combined_instruction = f.read() + "\n\n"

    # キャラクター固有定義の読み込み
    with open(persona_path, "r", encoding="utf-8") as f:
        combined_instruction += f.read()
    
    logger.info(f"Loaded core and persona for {name}")
    return combined_instruction

async def main():
    # テレメトリのセットアップ
    setup_telemetry()
    logger.info("Starting Saint Graph in Chat Mode...")

    # ペルソナ設定の読み込み
    system_instruction = load_persona(name="ren")

    # ニュースサービスの初期化
    news_path = "/app/data/news/news_script.md"
    from .news_service import NewsService
    news_service = NewsService(news_path)
    try:
        news_service.load_news()
        if not news_service.items:
            logger.warning(f"NewsService loaded 0 items from {news_path}.")
        else:
            logger.info(f"Loaded {len(news_service.items)} news items from {news_path}.")
    except Exception as e:
        logger.error(f"Failed to load news: {e}")

    # 進行用および再指示（Retry）用テンプレートの読み込み
    templates = {}
    prompts_dir = "/app/src/mind/ren/system_prompts"
    prompt_names = [
        "intro", "news_reading", "news_finished", "closing",
        "retry_no_tool", "retry_final_response"
    ]
    for name in prompt_names:
        path = os.path.join(prompts_dir, f"{name}.md")
        with open(path, "r", encoding="utf-8") as f:
            templates[name] = f.read()

    # SaintGraph (ADK) の初期化
    retry_templates = {k: v for k, v in templates.items() if k.startswith("retry_")}
    saint_graph = SaintGraph(
        mcp_urls=MCP_URLS, 
        system_instruction=system_instruction,
        retry_templates=retry_templates
    )

    # メインループの定義
    logger.info("Entering Newscaster Loop...")

    finished_news = False
    end_wait_counter = 0
    MAX_WAIT_CYCLES = 20 # インタラクション停止後の待機秒数

    # 配信開始の挨拶
    await saint_graph.process_turn(templates["intro"], context="Intro")

    while True:
        try:
            # 1. ユーザーからのコメント確認
            has_user_interaction = False
            try:
                comments = await saint_graph.call_tool("sys_get_comments", {})
                
                if comments and comments != "No new comments.":
                    logger.info(f"Comments received: {comments}")
                    # ユーザーの発言に反応
                    await saint_graph.process_turn(comments)
                    has_user_interaction = True
                    # インタラクションがあれば終了カウントをリセット
                    end_wait_counter = 0
            except Exception as e:
                if "Tool sys_get_comments not found" in str(e) or "not found in any toolset" in str(e):
                    logger.warning("Waiting for sys_get_comments tool to become available...")
                else:
                    logger.error(f"Error in polling/turn: {e}")

            # 2. ニュース読み上げ (ユーザーの割り込みがない場合)
            if not has_user_interaction:
                if news_service.has_next():
                    item = news_service.get_next_item()
                    logger.info(f"Reading news item: {item.title}")
                    
                    # ニュース読み上げ指示の生成
                    instruction = templates["news_reading"].format(title=item.title, content=item.content)
                    await saint_graph.process_turn(instruction, context=f"News Reading: {item.title}")
                    
                elif not finished_news:
                     # 全てのニュースを読み終えた直後の処理
                     finished_news = True
                     logger.info("All news items read. Waiting for final comments.")
                     await saint_graph.process_turn(
                         templates["news_finished"],
                         context="News Finished"
                     )
                
                elif finished_news:
                    # 終了シーケンスの待機カウント
                    end_wait_counter += 1
                    if end_wait_counter > MAX_WAIT_CYCLES:
                        logger.info(f"Silence timeout ({MAX_WAIT_CYCLES}s) reached. Finishing broadcast.")
                        await saint_graph.process_turn(
                             templates["closing"],
                             context="Closing"
                        )
                        # メッセージの送信完了を確実にするためのバッファ
                        await asyncio.sleep(3)
                        await saint_graph.close()
                        break

            # 監視間隔の待機
            await asyncio.sleep(POLL_INTERVAL)

        except Exception as e:
            logger.error(f"Unexpected error in Chat Loop: {e}", exc_info=True)
            await asyncio.sleep(5)
        except BaseException as e:
            logger.critical(f"Critical System Error: {e}", exc_info=True)
            raise

if __name__ == "__main__":
    import traceback
    try:
        asyncio.run(main())
    except Exception:
        traceback.print_exc()
        sys.stderr.flush()
        sys.stdout.flush()
