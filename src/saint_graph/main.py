import asyncio
import sys
import os

# モジュールのインポート
# 修正: news_reader は不要なので削除
from .config import logger, MCP_URL, POLL_INTERVAL
from .mcp_client import MCPClient
from .saint_graph import SaintGraph

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
    logger.info("Starting Saint Graph in Chat Mode...")

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

    # 5. メインループ (Chat Loop)
    logger.info("Entering Chat Loop. Waiting for comments...")

    while True:
        try:
            # 1. コメント確認
            comments = await client.call_tool("get_comments", {})
            
            if comments and comments != "No new comments.":
                logger.info("Comments received.")
                # ユーザーの発言として処理
                await saint_graph.process_turn(comments)

            # 定期ポーリングの間隔
            await asyncio.sleep(POLL_INTERVAL)

        except Exception as e:
            logger.error(f"Error in Chat Loop: {e}", exc_info=True)
            await asyncio.sleep(5) # エラー時は少し長く待機

if __name__ == "__main__":
    asyncio.run(main())
