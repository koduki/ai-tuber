# プロンプト設計

Saint Graph のプロンプトシステムについて説明します。

---

## プロンプトの分離

プロンプトは「システム命令」と「キャラクターペルソナ」に分離されています。

### システムプロンプト

**場所**: `src/saint_graph/system_prompts/`

**役割**: キャラクターに依存しない配信フローの共通ルール

**ファイル**:
- `core_instructions.md` - 基本原則（感情タグ、ツール利用）
- `intro.md` - 挨拶フェーズ
- `news_reading.md` - ニュース読み上げフェーズ
- `news_finished.md` - ニュース終了フェーズ
- `closing.md` - 終了フェーズ

### キャラクタープロンプト

**場所**: `data/mind/{character_name}/persona.md`

**役割**: キャラクター固有の性格、口調、個性

---

## core_instructions.md

基本原則を定義します。

### 主要ルール

1. **感情タグの付与**:
   ```
   レスポンスの先頭に必ず [emotion: <type>] を付けること
   対応する感情: neutral, joyful, fun, sad, angry
   ```

2. **外部ツールの使用**:
   ```
   天気情報が必要な場合は get_weather ツールを使用すること
   ```

3. **自然なテキスト生成**:
   ```
   speak ツールの直接呼び出しは不要
   自然なテキストを生成すれば、システムが自動的に発話に変換
   ```

---

## フェーズ別プロンプト

### intro.md（挨拶）

```markdown
あなたは配信を開始します。
視聴者に対して元気よく挨拶してください。

注意:
- キャラクターらしい挨拶をすること
- 今日の配信内容を簡単に紹介すること
- [emotion: joyful] から始めること
```

### news_reading.md（ニュース読み上げ）

```markdown
以下のニュースを解説してください。

ニュース:
{news_title}
{news_content}

注意:
- 専門用語はわかりやすく説明すること
- キャラクターの口調で語ること
- 適切な感情タグを付けること
```

### news_finished.md（ニュース終了）

```markdown
すべてのニュースの読み上げが終了しました。
視聴者に質問を募ってください。

注意:
- 視聴者とのコミュニケーションを促すこと
- キャラクターらしく締めくくること
```

### closing.md（終了）

```markdown
配信を終了します。
視聴者に感謝を伝えて、別れの挨拶をしてください。

注意:
- 感謝の気持ちを表すこと
- 次回の配信に期待を持たせること
- [emotion: joyful] または [emotion: neutral] で締めること
```

---

## プロンプトの結合

### prompt_loader.py

`PromptLoader` は **デュアルストレージ構成** を採用しています。

| データ種別 | ストレージ | 理由 |
|:---|:---|:---|
| **システムプロンプト** (`core_instructions.md`, テンプレート) | 常にローカル FS (コンテナイメージ内) | コードの一部、ビルド時に同梱 |
| **Mind データ** (`persona.md`, `mind.json`) | `StorageClient` 経由 (GCS or Local) | キャラクター固有データ、外部管理 |

```python
class PromptLoader:
    def __init__(self, character_name, storage_client=None):
        self.character_name = character_name
        self.storage = storage_client or create_storage_client()
        
        # システムプロンプト (src/...) はソースコードに同梱されているため、プロジェクトルートを基点とする
        from infra.storage_client import FileSystemStorageClient
        self.system_storage = FileSystemStorageClient(base_path=PROJECT_ROOT)

    def load_system_instruction(self):
        # システムプロンプト (ローカル FS)
        core = self.system_storage.read_text(
            key="src/saint_graph/system_prompts/core_instructions.md"
        )
        # ペルソナ (StorageClient 経由 - GCS または data/ ディレクトリ)
        persona = self.storage.read_text(
            key=f"mind/{self.character_name}/persona.md"
        )
        return core + "\n\n" + persona
```

### 使用例

```python
# PromptLoader は環境に応じて自動的に適切なストレージを使用
loader = PromptLoader(character_name="ren")
system_instruction = loader.load_system_instruction()
templates = loader.load_templates(["intro", "news_reading", "closing"])
mind_config = loader.load_mind_config()

# Agent に設定
agent = Agent(
    model=Gemini(model="gemini-2.5-flash-lite"),
    instruction=system_instruction,
    tools=tools
)
```

---

## mind.json の読み込み

キャラクター固有の技術設定を読み込みます。

### ファイル形式

```json
{
  "speaker_id": 58
}
```

### 読み込み

```python
# StorageClient 経由で GCS / ローカルどちらからも読み込み可能
loader = PromptLoader(character_name="ren")
mind_config = loader.load_mind_config()
speaker_id = mind_config.get("speaker_id")
```

---

## プロンプトのテスト

### test_prompt_loader.py

```python
def test_load_system_prompt():
    prompt = load_system_prompt("intro")
    assert "挨拶" in prompt

def test_load_character_prompt():
    prompt = load_character_prompt("ren")
    assert "紅月れん" in prompt

def test_load_mind_json():
    config = load_mind_config("ren")
    assert "speaker_id" in config
```

---

## 関連ドキュメント

- [README](./README.md) - Saint Graph 概要
- [Mind - Character System](../../components/mind/character-system.md) - キャラクター定義
- [Mind - Character Creation](../../components/mind/character-creation-guide.md) - キャラクター作成
