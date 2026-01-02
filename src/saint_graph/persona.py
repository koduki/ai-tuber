import os
from .config import logger

def load_persona() -> str:
    """
    persona.md ファイルを読み込んでシステム指示としての文字列を返します。
    """
    # 現在のファイルの位置から相対的に探索
    persona_path = os.path.join(os.path.dirname(__file__), "..", "mind", "ren", "persona.md")
    persona_path = os.path.normpath(persona_path)

    # 簡易的な探索ロジック
    if not os.path.exists(persona_path):
        paths_to_try = [
            "/workspaces/ai-tuber/src/mind/ren/persona.md",
            "src/mind/ren/persona.md",
            "mind/ren/persona.md"
        ]
        for p in paths_to_try:
            if os.path.exists(p):
                persona_path = p
                break

    try:
        with open(persona_path, "r", encoding="utf-8") as f:
            system_instruction = f.read()
            logger.info(f"Loaded persona from {persona_path}")
            return system_instruction
    except Exception as e:
        logger.error(f"Could not read persona file at {persona_path}: {e}")
        # フォールバック
        return "You are a helpful AI Tuber."
