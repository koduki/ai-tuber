# 開発者ガイド

このガイドでは、AI Tuber システムの開発環境のセットアップ、コードの編集、テストの実行方法を説明します。

---

## 開発環境のセットアップ

### 必要なツール

- **Python**: 3.11 以上
- **Docker** と **Docker Compose**
- **Git**
- **エディタ**: VS Code 推奨

### リポジトリのクローンとインストール

```bash
git clone https://github.com/koduki/ai-tuber.git
cd ai-tuber

# 依存関係のインストール（ローカル開発の場合）
pip install -r requirements.txt
```

---

## プロジェクト構成

```
ai-tuber/
├── scripts/
│   └── news_collector/    # ニュース収集エージェント
│       ├── news_agent.py  # 収集・要約・クリーンアップ
│       ├── requirements.txt
│       └── README.md
├── src/
│   ├── saint_graph/       # Saint Graph (魂) - Google ADK Agent
│   │   ├── main.py        # エントリポイント
│   │   ├── agent.py       # Agent 設定とターン処理
│   │   ├── body_client.py # Body REST クライアント
│   │   ├── prompts.py     # プロンプト読み込み
│   │   └── tools.py       # MCP ツール統合
│   ├── body/
│   │   ├── cli/           # Body CLI (開発用)
│   │   │   ├── main.py
│   │   │   └── server.py
│   │   └── streamer/      # Body Streamer (本番用)
│   │       ├── main.py
│   │       ├── server.py
│   │       ├── obs_client.py
│   │       ├── voice.py
│   │       └── youtube_comment_adapter.py
│   └── tools/
│       └── weather/       # Weather MCP Server
│           ├── main.py
│           └── server.py
├── data/
│   ├── mind/              # キャラクター定義
│   │   └── ren/           # デフォルトキャラクター
│   │       ├── mind.json  # 技術設定
│   │       ├── persona.md # 性格・口調
│   │       └── assets/    # 立ち絵・音声
│   └── news/              # ニュース原稿
├── tests/
│   ├── unit/              # ユニットテスト
│   ├── integration/       # 統合テスト
│   └── e2e/               # E2E テスト
├── docs/                  # ドキュメント
└── docker-compose.yml     # Docker 構成
```

---

## 開発ワークフロー

### 1. CLI モードでの開発

最も簡単な開発方法は CLI モードです。OBS や VoiceVox を起動せずに、テキストベースで対話できます。

```bash
# CLI モードで起動
docker compose up body-cli saint-graph tools-weather

# 別のターミナルで CLI に接続
docker attach ai-tuber-body-cli-1
```

入力例：
```
東京の天気を教えて
```

出力例：
```
[AI (neutral)]: 東京の天気の情報を確認するのじゃ...
[AI (joyful)]: 今日の東京は晴れのようじゃのう！
```

### 2. コードの編集

コードを編集したら、コンテナを再起動して変更を反映します。

```bash
# 特定のサービスを再起動
docker compose restart saint-graph

# または再ビルド
docker compose up --build saint-graph
```

### 3. ログの確認

```bash
# すべてのサービスのログを表示
docker compose logs -f

# 特定のサービスのログのみ
docker compose logs -f saint-graph
docker compose logs -f body-streamer
```

---

## テストの実行

### すべてのテストを実行

```bash
# テストコンテナを起動してテスト実行
docker compose run --rm saint-graph pytest

# または、ローカル環境で実行
pytest
```

### カテゴリ別にテストを実行

```bash
# ユニットテストのみ
pytest tests/unit/

# 統合テストのみ
pytest tests/integration/

# 特定のテストファイル
pytest tests/unit/test_saint_graph.py

# 特定のテスト関数
pytest tests/unit/test_saint_graph.py::test_parse_emotion_tag
```

### テストカバレッジ

```bash
# カバレッジレポートを生成
pytest --cov=src --cov-report=html

# ブラウザで確認
open htmlcov/index.html
```

### 現在のテスト構成

本システムには以下のテストが含まれています：

- **ユニットテスト** (11)
  - `test_prompt_loader.py` - mind.json 読み込み
  - `test_saint_graph.py` - AI 応答パース・感情制御
  - `test_obs_recording.py` - OBS 録画制御
  - `test_weather_tools.py` - 天気ツール
  - `test_news_collector.py` - ニュース収集エージェントのクリーンアップ

- **統合テスト** (15)
  - `test_speaker_id_integration.py` - speaker_id 伝播検証
  - `test_rest_body_cli.py` - Body CLI API
  - `test_newscaster_logic_v2.py` - ニュース配信フロー
  - `test_youtube_oauth.py` - YouTube OAuth 認証
  - `test_youtube_comment_adapter.py` - YouTube コメント取得

- **E2E テスト** (2)
  - `test_system_smoke.py` - システム全体動作確認（スキップ可能）

---

## 主要コンポーネントの開発

### Saint Graph（魂）の編集

**場所**: `src/saint_graph/`

**主な責務**:
- AI による意思決定
- Body への指令送信（REST）
- 外部ツールの活用（MCP）
- 感情パース処理

**編集例**: プロンプトの変更

```python
# src/saint_graph/prompts.py
def load_system_prompt(character_name: str, scene: str) -> str:
    """システムプロンプトを読み込む"""
    prompt_path = f"/app/data/mind/{character_name}/system_prompts/{scene}.md"
    with open(prompt_path, "r") as f:
        return f.read()
```

### Body（肉体）の編集

**場所**: `src/body/streamer/` または `src/body/cli/`

**主な責務**:
- 音声合成（VoiceVox）
- 映像制御（OBS）
- YouTube Live 配信
- REST API サーバー

**編集例**: 新しい感情を追加

```python
# src/body/streamer/obs_client.py
EMOTION_TO_IMAGE = {
    "neutral": "ai_neutral.png",
    "joyful": "ai_joyful.png",
    "fun": "ai_fun.png",
    "angry": "ai_angry.png",
    "sad": "ai_sad.png",
    "surprised": "ai_surprised.png",  # 新規追加
}
```

### Mind（精神）の編集

**場所**: `data/mind/{character_name}/`

**主な責務**:
- キャラクター定義
- プロンプト設定
- 感情と声の設定

**編集例**: 新しいキャラクターの追加

```bash
# 新しいキャラクターディレクトリを作成
mkdir -p data/mind/new_character/system_prompts
mkdir -p data/mind/new_character/assets

# 必要なファイルをコピー
cp data/mind/ren/mind.json data/mind/new_character/
cp data/mind/ren/persona.md data/mind/new_character/

# mind.json と persona.md を編集
# assets/ に立ち絵を追加

# 環境変数で切り替え
export CHARACTER_NAME=new_character
```

詳細は [キャラクター作成ガイド](../components/mind/character-creation-guide.md) を参照してください。

---

## デバッグ方法

### Python デバッガの使用

```python
# コードにブレークポイントを設定
import pdb; pdb.set_trace()

# または、Python 3.7 以降
breakpoint()
```

### コンテナ内でのシェルアクセス

```bash
# 実行中のコンテナに入る
docker compose exec saint-graph bash

# または、新しいシェルを起動
docker compose run --rm saint-graph bash
```

### ログレベルの変更

```python
# src/saint_graph/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## よくある開発タスク

### 新しい MCP ツールの追加

1. `src/tools/` に新しいディレクトリを作成
2. MCP サーバーを実装
3. `docker-compose.yml` にサービスを追加
4. `src/saint_graph/tools.py` で登録

### ニュース原稿の追加

```bash
# 新しいニュース原稿を追加
echo "今日は良い天気です。" > data/news/weather_news.txt

# Saint Graph が自動的に検出して読み上げます
```

### OBS シーンのカスタマイズ

1. VNC で OBS に接続: http://localhost:8080/vnc.html
2. シーンやソースを編集
3. **ファイル** → **設定をエクスポート** で保存
4. `src/body/streamer/obs/scene_config.json` を更新

---

## コーディング規約

### Python スタイル

- **PEP 8** に準拠
- **型ヒント** を使用
- **Docstring** を記述（Google スタイル）

```python
def speak(text: str, style: str = "neutral") -> dict:
    """テキストを発話する。

    Args:
        text: 発話するテキスト
        style: 感情スタイル (neutral, joyful, fun, angry, sad)

    Returns:
        API レスポンス

    Raises:
        ValueError: style が不正な場合
    """
    ...
```

### コミットメッセージ

```
feat: 新機能を追加
fix: バグ修正
docs: ドキュメント更新
test: テスト追加・修正
refactor: リファクタリング
```

---

## 環境変数リファレンス

開発時によく使う環境変数：

| 変数 | デフォルト | 説明 |
|------|-----------|------|
| `RUN_MODE` | `cli` | `cli` または `streamer` |
| `STREAMING_MODE` | `false` | YouTube 配信を有効化 |
| `CHARACTER_NAME` | `ren` | 使用するキャラクター名 |
| `NEWS_DIR` | `/app/data/news` | ニュース原稿ディレクトリ |
| `MODEL_NAME` | `gemini-2.5-flash-lite` | Gemini モデル |
| `ADK_TELEMETRY` | `false` | ADK テレメトリ |

詳細は [通信プロトコル](../architecture/communication.md) を参照してください。

---

## CI/CD（将来的に追加予定）

現在、GitHub Actions によるテスト自動化を検討中です。

---

## よくある質問

### Q: コードを変更したのに反映されない

**A**: Docker イメージを再ビルドしてください。

```bash
docker compose up --build
```

### Q: ローカルで Python を実行したい

**A**: 仮想環境を作成して依存関係をインストールしてください。

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Q: テストが失敗する

**A**: 依存サービスが起動しているか確認してください。

```bash
docker compose up -d body-cli
pytest tests/integration/test_rest_body_cli.py
```

---

## 関連ドキュメント

- [セットアップガイド](./setup.md) - 初期セットアップ
- [システム概要](../architecture/overview.md) - アーキテクチャ
- [通信プロトコル](../architecture/communication.md) - API 仕様
- [データフロー](../architecture/data-flow.md) - 処理シーケンス

---

**最終更新**: 2026-02-02
