import json
import os
from pathlib import Path
from typing import Optional
from .config import logger
from infra.storage_client import StorageClient, create_storage_client

# アプリケーションのルートパス (src directory)
APP_ROOT = Path(__file__).resolve().parent.parent
# データディレクトリ (project root/data)
DATA_ROOT = APP_ROOT.parent / "data"


class PromptLoader:
    """
    キャラクター固有およびシステム共通のプロンプトファイルを読み込むクラス。
    StorageClient を使用して、ローカル / GCS どちらからでも読み込み可能。
    """

    def __init__(
        self, 
        character_name: Optional[str] = None,
        storage_client: Optional[StorageClient] = None
    ):
        """
        PromptLoaderを初期化します。
        
        Args:
            character_name: 読み込むキャラクターの名前。
                          None の場合は CHARACTER_NAME 環境変数を使用（デフォルト: "ren"）
            storage_client: StorageClient インスタンス。None の場合は自動生成。
        """
        self.character_name = character_name or os.getenv("CHARACTER_NAME", "ren")
        self.storage = storage_client or create_storage_client()
        
        # システムプロンプト (src/...) はソースコードに同梱されているため、プロジェクトルートを基点とする
        from infra.storage_client import FileSystemStorageClient
        self.system_storage = FileSystemStorageClient(base_path=str(APP_ROOT.parent))
        
        # 論理的なベースパス（ストレージクライアントの基点からの相対パス）
        self._saint_graph_prompts_path = "src/saint_graph/system_prompts"
        self._mind_base_path = f"mind/{self.character_name}"
        
        logger.info(f"PromptLoader initialized for character: {self.character_name} (Logical path: {self._mind_base_path})")

    def load_system_instruction(self) -> str:
        """
        core_instructions.md と persona.md を結合してシステム指示を返します。
        """
        try:
            # core_instructions.md を読み込み（共通プロンプト） - Always from source code (Local FS)
            core_content = self.system_storage.read_text(
                key=f"{self._saint_graph_prompts_path}/core_instructions.md"
            )
            
            # persona.md を読み込み（キャラクター固有） - From Storage (Bucket or data/)
            persona_content = self.storage.read_text(
                key=f"{self._mind_base_path}/persona.md"
            )
            
            combined = core_content + "\n\n" + persona_content
            logger.info(f"Loaded core and persona for {self.character_name}")
            return combined
            
        except Exception as e:
            logger.error(f"Failed to load system instruction: {e}")
            raise

    def load_templates(self, names: list[str]) -> dict[str, str]:
        """
        指定された名前のテンプレートをsaint_graph配下から読み込みます。
        """
        templates = {}
        for name in names:
            try:
                # Templates are always from source code (Local FS)
                content = self.system_storage.read_text(
                    key=f"{self._saint_graph_prompts_path}/{name}.md"
                )
                templates[name] = content
            except Exception as e:
                logger.warning(f"Failed to load template '{name}': {e}")
        
        return templates

    def get_retry_templates(self, templates: dict[str, str]) -> dict[str, str]:
        """
        テンプレート辞書から再指示（retry_*）用のものだけを抽出します。
        """
        return {k: v for k, v in templates.items() if k.startswith("retry_")}

    def load_mind_config(self) -> dict:
        """
        mind.json からキャラクター設定を読み込みます。
        """
        try:
            content = self.storage.read_text(
                key=f"{self._mind_base_path}/mind.json"
            )
            return json.loads(content)
        except FileNotFoundError:
            logger.warning(f"mind.json not found for {self.character_name}")
            return {}
        except Exception as e:
            logger.error(f"Error loading mind.json for {self.character_name}: {e}")
            return {}

