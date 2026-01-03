import asyncio
import sys

# モジュールのインポート
from .config import logger, MCP_URL, NEWS_DIR
from .mcp_client import MCPClient
from .persona import load_persona
from .saint_graph import SaintGraph
from .news_reader import NewsReader

async def main():
    logger.info("Starting Saint Graph in News Delivery Mode...")

    # 1. Body (MCP) への接続
    await asyncio.sleep(2) # 接続待機
    client = MCPClient(base_url=MCP_URL)
    try:
        await client.connect()
    except Exception as e:
        logger.error(f"Failed to connect to MCP Body at {MCP_URL}: {e}")
        return

    # 2. Mind (Persona) の初期化
    system_instruction = load_persona(name="ren")

    # 3. ツールの定義 (動的取得)
    tool_definitions = client.get_google_genai_tools()
    logger.info(f"Loaded {len(tool_definitions[0].function_declarations) if tool_definitions else 0} tools from MCP.")

    # 4. Saint Graph の初期化
    saint_graph = SaintGraph(mcp_client=client, system_instruction=system_instruction, tools=tool_definitions)

    # 5. ニュース読み込み
    news_reader = NewsReader(NEWS_DIR)
    news_chunks = news_reader.get_latest_news_chunks()

    if not news_chunks:
        logger.warning(f"No news found in {NEWS_DIR}. Exiting.")
        return

    logger.info(f"Found {len(news_chunks)} news chunks. Starting delivery.")

    # 6. メインループ (News Loop)
    # 起動毎に固定のニュースを順番に処理して終了する
    try:
        for i, chunk in enumerate(news_chunks):
            # 1. コメント/割り込みチェック (Interruption Check)
            # ニュースを読む前に、常に新しいコメントがないか確認する ("適宜コメントを拾う")
            comments = await client.call_tool("get_comments", {})
            
            if comments and comments != "No new comments.":
                logger.info("Interruption detected (Comments found).")
                interruption_msg = f"[System/Interruption]:\nUser Comments:\n{comments}\n(Answer briefly and explicitly say 'それではニュースに戻るのじゃ' to resume)"
                await saint_graph.process_turn(interruption_msg)
                await asyncio.sleep(1)

            # 2. ニュース読み上げ (または指示の実行)
            logger.info(f"Processing news chunk {i+1}/{len(news_chunks)}")
            
            # チャンク自体に指示(例: [ここで短い雑談])が含まれている場合、LLMはその指示に従う
            news_msg = f"[System/NewsFeed] (Chunk {i+1}/{len(news_chunks)}):\n{chunk}"
            await saint_graph.process_turn(news_msg)

            # チャンク間の待機
            await asyncio.sleep(2)

        # 7. 終了処理
        logger.info("News delivery finished. Speaking closing words.")
        closing_msg = "[System/Instruction]: News ended. Speak closing words to the audience and say goodbye."
        await saint_graph.process_turn(closing_msg)

    except Exception as e:
        logger.error(f"Error in News Loop: {e}", exc_info=True)
    finally:
        logger.info("Exiting Saint Graph.")
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
