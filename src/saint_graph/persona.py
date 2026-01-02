import os
from .config import logger

def load_persona(name: str = "ren") -> str:
    """
    指定されたキャラクター名のpersona.mdファイルを読み込んでシステム指示として返します。
    探索は行わず、src/mind/{name}/persona.md を直接参照します。
    """
    # src/mind/{name}/persona.md を絶対パスで構築
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # src/
    persona_path = os.path.join(base_dir, "mind", name, "persona.md")
    persona_path = os.path.normpath(persona_path)

    try:
        with open(persona_path, "r", encoding="utf-8") as f:
            system_instruction = f.read()
            logger.info(f"Loaded persona from {persona_path}")
            return system_instruction
    except FileNotFoundError:
        logger.error(f"Persona file not found at {persona_path}")
        return "You are a helpful AI Tuber."
    except Exception as e:
        logger.error(f"Could not read persona file at {persona_path}: {e}")
        return "You are a helpful AI Tuber."
