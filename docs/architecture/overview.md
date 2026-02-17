# システム概要

AI Tuber は、**魂（Saint Graph）**、**肉体（Body）**、**精神（Mind）** の三位一体で構成される AITuber システムです。

## 三位一体アーキテクチャ

### Saint Graph（魂）
Google ADK をベースにした意思決定エンジン。システムの思考と対話を担当します。

**責任範囲**:
- AI による意思決定とターン処理
- ニュース原稿の管理と配信フロー制御
- Body への指令送信（REST Client）
- 外部ツールの活用（MCP Client）
- 感情パース処理

### Body（肉体）
ストリーミング制御ハブ。物理的な入出力と外部サービスとの連携を担当します。

**責任範囲**:
- 音声合成（VoiceVox）
- 映像制御（OBS Studio）
- YouTube Live 配信・コメント取得
- REST API サーバーの提供

**モード**:
- **Streamer モード**: 本番配信用（OBS + VoiceVox + YouTube）
- **CLI モード**: 開発・デバッグ用（標準入出力）

### Mind（精神）
キャラクター定義パッケージ。個性とペルソナを担当します。

**責任範囲**:
- キャラクターのペルソナ定義
- キャラクターのボイス設定（speaker_id など）
- アセット（画像・音声）の管理

---

## アーキテクチャ設計原則

本システムは、将来的な拡張性と保守性を考慮し、以下の設計原則に基づいて構築されています。

### 1. コードとデータの分離

**Mind（キャラクター定義）をデータとして扱う**ことで、コードの再利用性を最大化します。

- **Saint Graph** は汎用的な「思考エンジン」として実装
- **キャラクター設定**（persona.md、mind.json、アセット）は外部データとして管理
- キャラクターを追加・変更する際、コードの変更やコンテナの再ビルドは不要

```
コード (再利用可能)
  └─ SaintGraph エンジン
       ↓ 読み込み
データ (キャラクター固有)
  ├─ persona.md      # 性格・口調
  ├─ mind.json       # 技術設定（speaker_id等）
  └─ assets/         # 立ち絵・音声
```

### 2. ステートレスコンテナ

**コンテナイメージにユーザ固有情報を含めない**ことで、デプロイとスケーリングを柔軟に行えます。

- コンテナ起動時に `CHARACTER_NAME` 環境変数でキャラクターを指定
- プロンプトやアセットは起動時に `StorageClient` 経由で動的ロード（画像・BGM等も含む）
- API キーや認証情報は環境変数（Cloud Run / GCE 等が提供）経由で取得

**メリット**:
- イメージの再ビルドなしでキャラクター切り替え可能
- 機密情報がイメージに含まれない（セキュリティ向上）
- 将来的なマルチテナント化への対応が容易

### 3. プラットフォーム抽象化

**ローカル開発と本番環境の差異を吸収**することで、開発体験を統一します。

#### Storage Abstraction Layer

| 環境 | ストレージ | 認証 |
|------|-----------|------|
| **ローカル** | FileSystem (`./data/`) | 不要 |
| **本番 (GCP)** | Google Cloud Storage | IAM / Service Account |

`StorageClient` インターフェースにより、アプリケーションはストレージの実装詳細を意識せずに動作します。

**⚠️ GCS とローカルのパス規約の違い:**

`cloudbuild-mind.yaml` の同期コマンド `gsutil rsync data/mind/ gs://bucket/mind/` により、GCS 上のキーには `data/` プレフィクスが付きません。

| 環境 | `persona.md` のパス |
|------|---|
| **ローカル** | `{base}/data/mind/ren/persona.md` |
| **GCS** | `gs://bucket/mind/ren/persona.md` |

この差異は `PromptLoader` 内で `STORAGE_TYPE` 環境変数に基づき自動的に吸収されます。

#### Secrets Management
 
 本システムは、実行環境（Cloud Run や GCE）が提供する環境変数を直接利用する設計を採用しています。これにより、インフラレイヤーでセキュアに注入された値をアプリケーションコードが透過的に利用できます。
 
 **ADK 連携:** Google ADK は `os.environ["GOOGLE_API_KEY"]` を直接参照するため、実行環境から提供されたキーをそのまま利用します。

---

## システム構成

### マイクロサービス構成

| サービス | 役割 | ポート | 通信方式 |
|---------|------|--------|---------|
| `saint-graph` | 思考・対話エンジン（魂） | - | REST Client / MCP Client |
| `body-streamer` | ストリーミング制御ハブ（肉体） | 8002 | REST API Server |
| `body-cli` | 開発用 CLI 入出力（肉体） | 8000 | REST API Server |
| `tools-weather` | 天気情報取得ツール（AI自律ツール） | 8001 | MCP Server (SSE) |
| `health-proxy` | システム監視・疎通確認プロキシ | 8080 | REST API |
| `obs-studio` | 配信・映像合成 | 8080, 4455 | VNC / WebSocket |
| `voicevox` | 音声合成エンジン | 50021 | HTTP API |
| `news-collector` | ニュース自動収集バッチ | - | Cloud Run Job |

### システムマップ

```mermaid
graph TD
  subgraph Mind ["Mind (精神)"]
    Persona["data/mind/{name}/persona.md"]
    MindJson["data/mind/{name}/mind.json"]
    Assets["data/mind/{name}/assets/"]
    NewsScript["data/news/news_script.md"]
  end

  subgraph Tools ["Tools (Autonomous AI Tools)"]
    WeatherMcp["src/tools/weather/"]
    NoteTools["AIが自律判断で使用するツール(MCP等)のみを配置"]
  end

  subgraph Scripts ["Scripts & Internal Jobs"]
    NewsCollector["scripts/news_collector/news_agent.py"]
  end

  subgraph SaintGraph ["Saint Graph (魂)"]
    Agent["ADK Agent"]
    Runner["InMemoryRunner"]
- [emotion: type])"]
    BodyClient["REST BodyClient (System Logic)"]
    Toolset["McpToolset (Autonomous Extension)"]
  end

  subgraph BodyServices ["Body (肉体 / REST API)"]
    ServerStreamer["body-streamer (REST)"]
    ServerCLI["body-cli (REST)"]
  end

  subgraph Tools ["External Tools (MCP)"]
    ServerWeather["tools-weather (MCP Server)"]
  end
  
  subgraph ExternalServices ["外部サービス"]
    OBS["OBS Studio"]
    VoiceVox["VoiceVox Engine"]
    YouTube["YouTube Live API"]
    GoogleSearch["Google Search API"]
  end

  NewsCollector -- "Google Search" --> GoogleSearch
  NewsCollector -- "Write Markdown" --> NewsScript

  Persona -- "Instruction" --> Agent
  MindJson -- "Settings" --> Agent
  Assets -- "Resources" --> Agent
  Agent -- "Text Output" --> Parser
  Parser -- "REST/身体操作" --> BodyClient
  BodyClient -- "REST/身体操作" --> ServerStreamer
  BodyClient -- "REST/身体操作" --> ServerCLI
  
  Agent -- "自律的ツール利用 (MCP)" --> Toolset
  Toolset -- "MCP (SSE)" --> ServerWeather
  
  ServerStreamer -- "HTTP API" --> VoiceVox
  ServerStreamer -- "WebSocket" --> OBS
  ServerStreamer -- "OAuth + REST API" --> YouTube
```

---

## デプロイ環境

本システムは、異なる環境に応じて最適化された構成でデプロイできます。

### ローカル開発環境 (Docker Compose)

すべてのコンポーネントを単一のホスト上で実行します。

- **構成**: `docker-compose.yml` を使用
- **用途**: 開発、テスト、デバッグ
- **特徴**: すべてのサービスが同じネットワーク上で通信

### GCP 本番環境 (ハイブリッド構成)

マイクロサービスを役割に応じて最適なGCPサービスに配置します。

| サービス | GCP サービス | 理由 |
|---------|-------------|------|
| **Saint Graph** | **Cloud Run Job** | バッチ処理（配信）、最大24時間タイムアウト |
| Tools Weather | Cloud Run Service | ステートレス、MCP Server |
| News Collector | Cloud Run Job | 毎朝のバッチ処理（ニュース収集） |
| Body (OBS + VoiceVox + Streamer) | **Compute Engine + GPU** | GPU共有、高速ファイルアクセス |

**主な特徴**:
- ✅ **自動化**: Cloud Workflows による堅牢な配信パイプライン
  - 08:00: Cloud Scheduler がワークフローを起動
  - Step 1: ニュース収集ジョブ（Cloud Run Job）を実行
  - Step 2: Body Node (GCE) を起動し、**起動完了まで自動待機**
  - Step 3: Saint Graph (Cloud Run Job) を実行し配信開始
  - Step 4: 配信完了後、Body Node を自動停止してコスト削減
- ✅ **Infrastructure as Code**: OpenTofu で完全に管理
- ✅ **共有ストレージ**: Cloud Storage でニュース原稿を共有
- ✅ **Secret Manager 統合**: API キーや YouTube 認証情報を安全に管理
- ✅ **Git 不要**: Artifact Registry から直接イメージをプル
- ✅ **CI/CD 自動化**: Cloud Build によるディレクトリ単位の自動ビルド・デプロイ

**Saint Graph を Job として実装した理由**:
- HTTP サーバーの実装が不要（コードがシンプル）
- タイムアウトが最大 24 時間（Cloud Run Service は 60 分まで）
- バッチ処理（配信）としての実態に即している
- ヘルスチェック不要で堅牢

詳細: **[GCP デプロイガイド](../../opentofu/README.md)** / **[CI/CD アーキテクチャ](./cicd.md)**

---

## ハイブリッド REST/MCP アーキテクチャ

システムは役割に応じて通信プロトコルを使い分けます。

### REST API（Body 操作用）

**用途**: 確実に実行しなければならない、**「アプリケーション・ワークフロー」としての身体操作**

- 発話（speak）
- 表情変更（change_emotion）
- コメント取得（get_comments）
- 録画・配信制御（broadcast/start, broadcast/stop）

**特徴**:
- アプリケーション側のロジック（`main.py` 等）によって一律に制御される
- **Streamer モード**: 内部キューによる順次実行（API 呼び出し自体は非ブロッキング）
- 他のモード: 同期的な実行
- エラーハンドリングの統一

### MCP（外部ツール用）

**用途**: **AI（LLM）が自律的に判断して使う**「情報取得ツール」

- 天気予報（get_weather）
- 将来的に追加される知識検索など

**特徴**:
- AI の判断に基づき、必要に応じて呼び出される
- 動的なツール発見
- スキーマ駆動

---

## コンポーネント間の依存関係

```
Saint Graph (魂)
  ├─ depends on → Body (REST API)
  ├─ depends on → Tools (MCP)
  └─ uses → Mind (ファイル読み込み)

Body (肉体)
  ├─ controls → OBS Studio
  ├─ controls → VoiceVox
  ├─ integrates → YouTube Live
  └─ serves → REST API

Mind (精神)
  └─ provides → Character definitions
```

**疎結合の原則**:
- Saint Graph は Body の実装詳細を知らない（REST API のみ）
- Body は複数のモード（CLI/Streamer）を持てる
- Mind はプラグイン型で交換可能

---

## 配信フロー

`broadcast_loop.py` のステートマシンにより制御されます。

1. **初期化** (`main.py`): Saint Graph が Body と MCP Tools に接続、配信開始
2. **INTRO**: キャラクターが自己紹介
3. **NEWS**: コメント優先確認 → ニュース原稿を 1 本ずつ読み上げ
4. **IDLE**: ニュース終了後、コメント待機（タイムアウトで CLOSING へ）
5. **CLOSING**: クロージング挨拶 → 配信停止

各フェーズでコメントに応答できるため、ニュースの合間に視聴者とのインタラクションが可能です。

詳細は [data-flow.md](./data-flow.md) を参照してください。

---

---

## テスト

本システムは、ユニットテスト、統合テスト、および E2E テストによってカバーされています。

### テスト構成

```
tests/
├── unit/              # ユニットテスト
│   ├── test_broadcast_loop.py     # 配信ステートマシン
│   ├── test_prompt_loader.py      # mind.json 読み込み
│   ├── test_saint_graph.py        # AI 応答パース・感情制御
│   ├── test_obs_recording.py      # OBS 録画制御
│   ├── test_weather_tools.py      # 天気ツール
│   └── test_news_collector.py     # ニュース収集エージェント
├── integration/       # 統合テスト
│   ├── test_speaker_id_integration.py  # speaker_id 伝播検証
│   ├── test_rest_body_cli.py           # Body CLI API
│   ├── test_newscaster_logic_v2.py     # ニュース配信フロー
│   ├── test_newscaster_flow.py         # ニュース読み上げ
│   ├── test_mind_prompts.py            # プロンプト読み込み
│   ├── test_youtube_oauth.py           # YouTube OAuth 認証
│   ├── test_youtube_comment_adapter.py  # YouTube コメント取得
│   └── test_agent_scenarios.py         # 天気+発話シナリオ
├── infra/             # インフラ抽象化レイヤーテスト
│   ├── test_storage_client.py     # StorageClient (FileSystem / GCS)
│   └── test_secret_provider.py    # SecretProvider (Env / GCP)
└── e2e/               # E2E テスト
    └── test_system_smoke.py        # システム全体動作確認
```

### テスト実行

```bash
# 全テスト実行
pytest

# カテゴリ別
pytest tests/unit/
pytest tests/integration/
```

詳細は [README.md](../../README.md#テストの実行) を参照してください。

---

## 関連ドキュメント

- [通信プロトコル](./communication.md) - REST/MCP 仕様
- [データフロー](./data-flow.md) - 処理シーケンス
- [Saint Graph](../components/saint-graph/README.md) - 魂の詳細
- [Body](../components/body/README.md) - 肉体の詳細
- [Mind](../components/mind/README.md) - 精神の詳細
