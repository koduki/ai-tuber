# AI Tuber

**魂（Saint Graph）、肉体（Body）、精神（Mind）** の三位一体で構成される AITuber システムです。

AIニュースキャスターとしてコアロジックの魂が構成されており、CLIとOBSベースのYoutube配信を肉体として持ちます。精神はキャラクターの特徴や立ち絵、声などを表していて、これをプラガブルに組み替えることで、全体の構成を変えずに任意のキャラクターのAITuberを作成できます。
Saint GraphはMCPによる拡張可能です。

## 特徴

- **3層アーキテクチャ**: 魂・肉体・精神が分離された設計
- **ハイブリッド通信**: REST（身体操作）+ MCP（外部ツール）
- **YouTube Live 対応**: OAuth 認証、配信作成、リアルタイムコメント取得
- **感情制御**: AI 生成テキストから感情タグを自動パース
- **センテンス順次再生**: 音声の重複を防ぐインテリジェントな再生システム
- **プラグイン型キャラクター**: 新キャラクターの追加が容易

## Quick Start

### 1. 動作モードの選択

本システムは環境変数 `STREAMING_MODE` で動作を切り替えられます。

- **録画モード** (`STREAMING_MODE=false`): OBS での録画のみ。
- **配信モード** (`STREAMING_MODE=true`): YouTube Live での配信とコメント取得。

### 2. 環境変数の設定

`.env` ファイルを作成し、必要な情報を設定してください：

```bash
# 必須
GOOGLE_API_KEY="your_gemini_api_key"
STREAMING_MODE=false # false=録画, true=配信

# 配信設定 (STREAMING_MODE=true の場合のみ必須)
YOUTUBE_CLIENT_SECRET_JSON='{"installed":{...}}'
YOUTUBE_TOKEN_JSON='{"token":"...","refresh_token":"..."}'
STREAM_TITLE="本日のライブ配信"
```

### 3. 起動

```bash
# 本番配信・録画モード（Streamer）
docker compose up --build

# または開発モード（CLI）
docker compose up body-cli saint-graph
```

### 4. アクセス

- **OBS Studio**: http://localhost:8080/vnc.html (VNC)
- **Body API**: http://localhost:8002 (Streamer) / 8000 (CLI)
- **CLI 対話**: `docker attach app-body-cli-1`

## アーキテクチャ

### 三位一体構造

| コンポーネント | 役割 | 技術 |
|--------------|------|------|
| **Saint Graph（魂）** | 意思決定・対話 | Google Gemini ADK, MCP Client |
| **Body（肉体）** | 入出力・制御 | VoiceVox, OBS, YouTube API |
| **Mind（精神）** | キャラクター定義 | Markdown, JSON, アセット |

### マイクロサービス

| サービス | ポート | 説明 |
|---------|--------|------|
| `saint-graph` | - | 思考エンジン（魂） |
| `body-streamer` | 8002 | 本番配信用（肉体） |
| `body-cli` | 8000 | 開発用 CLI（肉体） |
| `tools-weather` | 8001 | 天気ツール（MCP） |
| `obs-studio` | 8080, 4455 | 映像合成 |
| `voicevox` | 50021 | 音声合成 |

詳細: [システム概要](docs/architecture/overview.md)

## 開発

### CLI モードでの対話

```bash
docker attach app-body-cli-1
# 入力: こんにちは
# 出力: [AI (joyful)]: 面を上げよ！わらわこそが紅月れんじゃ！
```

### テスト実行

```bash
# 全テスト
pytest

# ユニット/統合テストのみ
pytest tests/unit/
pytest tests/integration/
```

**テストカバレッジ**: 28テスト（ユニット: 11、統合: 15、E2E: 2）

主要テスト:
- `test_saint_graph.py` - AI応答パース・感情制御
- `test_speaker_id_integration.py` - VoiceVox speaker_id 伝播
- `test_youtube_oauth.py` - YouTube OAuth 認証
- `test_youtube_comment_adapter.py` - コメント取得

## キャラクター追加

```bash
data/mind/{character_name}/
├── mind.json          # 技術設定（speaker_id など）
├── persona.md         # 性格・口調
└── assets/            # 画像・音声
    ├── ai_neutral.png
    ├── ai_joyful.png
    └── ...
```

詳細: [キャラクター作成ガイド](docs/components/mind/character-creation-guide.md)

## 主な環境変数

### Saint Graph（魂）

| 変数 | デフォルト | 説明 |
|------|-----------|------|
| `GOOGLE_API_KEY` | (必須) | Gemini API キー |
| `STREAMING_MODE` | `false` | `true` で YouTube 配信, `false` で録画 |
| `RUN_MODE` | `cli` | `cli` または `streamer` |
| `MODEL_NAME` | `gemini-2.5-flash-lite` | 使用モデル |
| `STREAM_TITLE` | - | 配信タイトル |
| `STREAM_PRIVACY` | `private` | 配信公開設定 (`public`, `unlisted`, `private`) |
| `CHARACTER_NAME` | `ren` | キャラクター名 |
| `NEWS_DIR` | `/app/data/news` | ニュース原稿ディレクトリ |

### Body（肉体）

| 変数 | デフォルト | 説明 |
|------|-----------|------|
| `VOICEVOX_HOST` | `voicevox` | VoiceVox ホスト |
| `OBS_HOST` | `obs-studio` | OBS WebSocket ホスト |
| `YOUTUBE_CLIENT_SECRET_JSON` | - | OAuth 認証情報 |
| `YOUTUBE_TOKEN_JSON` | - | OAuth トークン |

詳細: [通信プロトコル](docs/architecture/communication.md)

## デプロイ

### ローカル開発

上記の Quick Start を参照してください。

### GCP 本番環境

クラウド上で自動運用するための完全な構成です：

**システム構成図**:
```
┌─────────────────────────────────────────────────────┐
│           Cloud Scheduler (毎朝自動実行)              │
│  07:00 News  →  07:55 GCE起動  →  08:00 配信開始     │
│                                 →  08:40 GCE停止    │
└─────────────────────────────────────────────────────┘
                        ↓
    ┌───────────────────────────────────────────┐
    │        Serverless Layer (Cloud Run)       │
    │  ┌──────────────────┐  ┌──────────────┐  │
    │  │ Saint Graph (Job)│  │Tools Weather │  │
    │  │  (配信ジョブ)      │  │ (Service)     │  │
    │  └──────────────────┘  └──────────────┘  │
    │  ┌──────────────────┐                    │
    │  │ News Collector   │  (Cloud Run Job)   │
    │  │ (ニュース収集)     │                    │
    │  └──────────────────┘                    │
    └───────────────────────────────────────────┘
                ↓                    ↓
    ┌─────────────────────┐  ┌──────────────┐
    │  Cloud Storage (GCS) │  │   Body Node  │
    │  - news_script.md    │  │  (Compute    │
    │  - 音声ファイル       │  │   Engine)    │
    └─────────────────────┘  │  + GPU       │
         ↑                   │  ┌─────────┐ │
         └───────────────────┼─→│Streamer │ │
                             │  │VoiceVox │ │
                             │  │  OBS    │ │
                             │  └─────────┘ │
                             └──────────────┘
                                    ↓
                            ┌──────────────┐
                            │ YouTube Live │
                            └──────────────┘
```

**主な特徴**:
- ✅ **自動化**: 毎朝決まった時間に自動でニュース収集・配信
  - 07:00: News Collector がニュース収集し GCS に保存
  - 07:55: Body Node (GCE) 起動、OBS と VoiceVox 準備完了
  - 08:00: Saint Graph (Cloud Run Job) 実行、配信開始
  - 08:40: Body Node (GCE) 停止、配信終了
- ✅ **コスト最適化**: Spot インスタンス使用で 60-90% コスト削減
- ✅ **スケール to Zero**: 使用していない時間は課金なし
- ✅ **Infrastructure as Code**: OpenTofu で完全に管理

**デプロイガイド**: **[opentofu/README.md](opentofu/README.md)**

## ドキュメント

| カテゴリ | ドキュメント |
|---------|-------------|
| **全体** | [ドキュメント一覧](docs/README.md) |
| **アーキテクチャ** | [システム概要](docs/architecture/overview.md), [通信プロトコル](docs/architecture/communication.md), [データフロー](docs/architecture/data-flow.md) |
| **Saint Graph（魂）** | [README](docs/components/saint-graph/README.md), [コアロジック](docs/components/saint-graph/core-logic.md), [プロンプト設計](docs/components/saint-graph/prompts.md) |
| **Body（肉体）** | [README](docs/components/body/README.md) |
| **Mind（精神）** | キャラクター作成ガイド（作成予定） |
