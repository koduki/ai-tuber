import asyncio

# モジュールのインポート
from .config import logger, RUN_MODE, MCP_URL, POLL_INTERVAL, SOLILOQUY_INTERVAL
from .mcp_client import MCPClient
from .persona import load_persona
from .tools import get_tool_definitions
from .saint_graph import SaintGraph

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

    while True:
        try:
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
