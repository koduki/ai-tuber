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

    # 2. Saint Graph (ADK) の初期化
    # McpToolset の初期化と接続管理は SaintGraph クラス内で行われます
    saint_graph = SaintGraph(mcp_urls=MCP_URLS, system_instruction=system_instruction)

    # 3. メインループ (Chat Loop)
    logger.info("Entering Chat Loop. Waiting for comments...")

    while True:
        try:
            # 1. コメント確認
            comments = await saint_graph.call_tool("sys_get_comments", {})
            
            if comments and comments != "No new comments.":
                logger.info("Comments received.")
                # ユーザーの発言として処理
                await saint_graph.process_turn(comments)

            # 定期ポーリングの間隔
            await asyncio.sleep(POLL_INTERVAL)

        except Exception as e:
            logger.error(f"Error in Chat Loop: {e}", exc_info=True)
            await asyncio.sleep(5) # エラー時は少し長く待機
        except BaseException as e:
            logger.critical(f"Critical Error in Chat Loop: {e}", exc_info=True)
            raise

if __name__ == "__main__":
    import traceback
    try:
        asyncio.run(main())
    except Exception:
        traceback.print_exc()
        sys.stderr.flush()
        sys.stdout.flush()
