import asyncio
import sys
import os

# モジュールのインポート
# 修正: news_reader は不要なので削除
from .config import logger, MCP_URLS, POLL_INTERVAL
from .saint_graph import SaintGraph
from .telemetry import setup_telemetry

def load_persona(name: str = "ren") -> str:
    """
    指定されたキャラクター名のpersona.mdファイルを読み込み、共通のcore_instructions.mdと結合してシステム指示として返します。
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # src/
    
    # Core Instructions
    core_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "core_instructions.md")

    # Persona
    persona_path = os.path.join(base_dir, "mind", name, "persona.md")
    persona_path = os.path.normpath(persona_path)

    try:
        combined_instruction = ""
        # Load Core
        if os.path.exists(core_path):
            with open(core_path, "r", encoding="utf-8") as f:
                combined_instruction += f.read() + "\n\n"
        else:
            logger.warning(f"Core instructions not found at {core_path}")

        # Load Persona
        with open(persona_path, "r", encoding="utf-8") as f:
            persona_content = f.read()
            logger.info(f"Loaded persona from {persona_path}")
            combined_instruction += persona_content
            
            return combined_instruction
    except FileNotFoundError:
        logger.error(f"Persona file not found at {persona_path}")
        return "You are a helpful AI Tuber."
    except Exception as e:
        logger.error(f"Could not read persona file at {persona_path}: {e}")
        return "You are a helpful AI Tuber."

async def main():
    setup_telemetry()
    logger.info("Starting Saint Graph in Chat Mode...")

    # 1. Mind (Persona) の初期化
    system_instruction = load_persona(name="ren")

    # 1.5 News Service の初期化
    # Get the directory of main.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up 2 levels: src/saint_graph -> src -> /app
    root_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
    news_path = os.path.join(root_dir, "data", "news", "news_script.md")
    
    from .news_service import NewsService
    news_service = NewsService(news_path)
    try:
        news_service.load_news()
        if not news_service.items:
            logger.warning(f"NewsService loaded 0 items from {news_path}. Check file format.")
        else:
            logger.info(f"Loaded {len(news_service.items)} news items from {news_path}.")
    except Exception as e:
        logger.error(f"Failed to load news: {e}")

    # 2. Saint Graph (ADK) の初期化
    saint_graph = SaintGraph(mcp_urls=MCP_URLS, system_instruction=system_instruction)

    # 3. メインループ (Chat Loop)
    logger.info("Entering Newscaster Loop...")

    # State for ending
    finished_news = False
    end_wait_counter = 0
    MAX_WAIT_CYCLES = 20 # 20 seconds of silence from the last interaction

    while True:
        try:
            # 1. コメント確認
            has_user_interaction = False
            try:
                comments = await saint_graph.call_tool("sys_get_comments", {})
                
                if comments and comments != "No new comments.":
                    logger.info(f"Comments received: {comments}")
                    # ユーザーの発言として処理
                    await saint_graph.process_turn(comments)
                    has_user_interaction = True
                    # コメントがあれば待機時間をリセット
                    end_wait_counter = 0
            except Exception as e:
                if "Tool sys_get_comments not found" in str(e) or "not found in any toolset" in str(e):
                    logger.warning("Waiting for sys_get_comments tool to become available...")
                else:
                    logger.error(f"Error in polling/turn: {e}")

            # 2. ニュース読み上げ (ユーザー介入がない場合)
            if not has_user_interaction:
                if news_service.has_next():
                    item = news_service.get_next_item()
                    logger.info(f"Reading news item: {item.title}")
                    
                    # Construct instruction for the agent
                    instruction = (
                        f"【システム指示：ニュース読み上げ】\n"
                        f"以下の「ニュース本文」を、一字一句省略せずに読み上げた上で、一連の発言として感想を述べてください。\n"
                        f"導入、本文、感想を**すべて1回**の `speak` ツール呼び出しにまとめて出力してください。\n"
                        f"\n"
                        f"ニュースタイトル: {item.title}\n"
                        f"ニュース本文:\n{item.content}\n"
                    )
                    
                    await saint_graph.process_turn(instruction, context=f"News Reading: {item.title}")
                    
                elif not finished_news:
                     # Just finished news items
                     finished_news = True
                     logger.info("All news items read. Waiting for final comments.")
                     await saint_graph.process_turn(
                         "【システム指示】\nすべてのニュースを読み終えました。「以上で本日のニュースを終わります」と伝えつつ、視聴者から最後に感想がないかあなたの口調（のじゃ/わらわ）で問いかけてください。",
                         context="News Finished"
                     )
                
                elif finished_news:
                    # Closing sequence logic: Incremented when NO interaction and NO news
                    end_wait_counter += 1
                    if end_wait_counter > MAX_WAIT_CYCLES:
                        logger.info(f"Silence timeout ({MAX_WAIT_CYCLES}s) reached. Finishing broadcast.")
                        await saint_graph.process_turn(
                            "【システム指示】\nしばらく待ちましたがコメントはありません。\n"
                            "「それでは、本日の放送を終了します。ありがとうございました！」とあなたの口調（のじゃ/わらわ）で最後の方に心を込めて挨拶し、配信を終了してください。これが最後の発言です。",
                             context="Closing"
                        )
                        # 送信完了を確実にするため少し待機
                        await asyncio.sleep(3)
                        await saint_graph.close()
                        break


            # 定期ポーリングの間隔
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
