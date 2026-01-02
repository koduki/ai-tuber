import asyncio

# モジュールのインポート
from .config import logger, RUN_MODE, MCP_URL, POLL_INTERVAL, SOLILOQUY_INTERVAL, NEWS_DIR
from .mcp_client import MCPClient
from .persona import load_persona
from .tools import get_tool_definitions
from .saint_graph import SaintGraph
from .news_reader import NewsReader

async def main():
    logger.info(f"Starting Saint Graph in {RUN_MODE} mode (Modular Refactored)...")

    # 1. Body (MCP) への接続
    await asyncio.sleep(2) # 接続待機
    client = MCPClient(base_url=MCP_URL)
    try:
        await client.connect()
    except Exception as e:
        logger.error(f"Failed to connect to MCP Body at {MCP_URL}: {e}")
        return

    # 2. Mind (Persona) の初期化
    # デフォルトで 'ren' を読み込むが、将来的に設定変更可能にする
    system_instruction = load_persona(name="ren")

    # 3. ツールの定義
    tool_definitions = get_tool_definitions()

    # 4. Saint Graph の初期化
    saint_graph = SaintGraph(mcp_client=client, system_instruction=system_instruction, tools=tool_definitions)

    # 5. メインループ (Outer Loop)
    poll_count = 0
    news_reader = NewsReader("/app/data/news")
    # Store processed news files to avoid reading them repeatedly in the loop
    # In a production system, this state should probably persist or files should be moved.
    # For this MVP, we will cache the latest file processing in memory.
    last_news_content = None

    while True:
        try:
            # --- ニュース配信モード ---
            # ニュースがあるかチェック
            news_chunks = news_reader.get_latest_news_chunks()

            # ニュースの内容が変わった場合のみ配信（簡易的な重複防止）
            # chunksを結合してハッシュ代わりにする
            current_news_content = "".join(news_chunks) if news_chunks else None

            if news_chunks and current_news_content != last_news_content:
                logger.info("New news found. Starting News Delivery Mode.")
                last_news_content = current_news_content

                for i, chunk in enumerate(news_chunks):
                    # 1. 割り込みチェック (Interruption Check)
                    comments = await client.call_tool("get_comments", {})
                    if comments and comments != "No new comments.":
                        logger.info("Interruption detected.")
                        interruption_msg = f"[System/Interruption]:\nUser Comments:\n{comments}\n(Answer briefly and explicitly say 'それではニュースに戻るのじゃ' to resume)"
                        await saint_graph.process_turn(interruption_msg)
                        await asyncio.sleep(1)

                    # 2. ニュース読み上げ (Read News Chunk)
                    logger.info(f"Reading news chunk {i+1}/{len(news_chunks)}")
                    news_msg = f"[System/NewsFeed] (Chunk {i+1}/{len(news_chunks)}):\n{chunk}"
                    await saint_graph.process_turn(news_msg)

                    # チャンク間の少し長い間
                    await asyncio.sleep(2)

                # ニュース終了後はコメント待ち受けに戻る
                continue

            # --- 通常モード (雑談待ち受け) ---
            # 観察: Bodyから新しいコメントを取得 (ポーリング)
            comments = await client.call_tool("get_comments", {})
            
            # Saint Graphを起動するか判定
            has_comments = comments != "No new comments."
            is_time_for_soliloquy = (poll_count * POLL_INTERVAL) >= SOLILOQUY_INTERVAL
            
            if not has_comments and not is_time_for_soliloquy:
                poll_count += 1
                await asyncio.sleep(POLL_INTERVAL)
                continue

            # カウンターリセット
            poll_count = 0
            
            # コンテキスト構築
            user_message = f"[System/Observation]:\nUser Comments:\n{comments}"
            
            # Saint Graphにターンを委譲 (Inner Loop)
            await saint_graph.process_turn(user_message)

            # 連続投稿を防ぐための短い待機
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Error in Main Loop: {e}", exc_info=True)
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
