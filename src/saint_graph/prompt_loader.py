from pathlib import Path
from .config import logger

# アプリケーションのルートパス (src directory)
APP_ROOT = Path(__file__).resolve().parent.parent
# データディレクトリ (project root/data)
DATA_ROOT = APP_ROOT.parent / "data"


class PromptLoader:
    """
    キャラクター固有およびシステム共通のプロンプトファイルを読み込むクラス。
    """

    def __init__(self, character_name: str = "ren"):
        """
        PromptLoaderを初期化します。
        
        Args:
            character_name: 読み込むキャラクターの名前（data/mindディレクトリ配下のフォルダ名）
        """
        self.character_name = character_name
        self._saint_graph_prompts_dir = APP_ROOT / "saint_graph" / "system_prompts"
        self._mind_prompts_dir = DATA_ROOT / "mind" / character_name / "system_prompts"
        self._persona_path = DATA_ROOT / "mind" / character_name / "persona.md"

    def load_system_instruction(self) -> str:
        """
        core_instructions.md と persona.md を結合してシステム指示を返します。
        """
        core_path = self._saint_graph_prompts_dir / "core_instructions.md"
        
        with open(core_path, "r", encoding="utf-8") as f:
            combined = f.read() + "\n\n"

        with open(self._persona_path, "r", encoding="utf-8") as f:
            combined += f.read()
        
        logger.info(f"Loaded core and persona for {self.character_name}")
        return combined

    def load_templates(self, names: list[str]) -> dict[str, str]:
        """
        指定された名前のテンプレートをMind配下から読み込みます。
        
        Args:
            names: 読み込むテンプレート名のリスト（拡張子なし）
        
        Returns:
            テンプレート名をキー、内容を値とする辞書
        """
        templates = {}
        for name in names:
            path = self._mind_prompts_dir / f"{name}.md"
            with open(path, "r", encoding="utf-8") as f:
                templates[name] = f.read()
        return templates

    def get_retry_templates(self, templates: dict[str, str]) -> dict[str, str]:
        """
        テンプレート辞書から再指示（retry_*）用のものだけを抽出します。
        """
        return {k: v for k, v in templates.items() if k.startswith("retry_")}
