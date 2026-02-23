# Saint Graph（魂）

Saint Graph は AI Tuber システムの「魂」であり、意思決定エンジンです。

---

## 役割と責任

**Saint Graph の役割**:
- **思考**: Google Gemini（ADK）を使用した AI 対話
- **意思決定**: ニュース配信フローの制御
- **指令**: Body への操作指示
- **ツール活用**: 外部ツール（天気など）の自律的な使用

**責任範囲**:
- ニュース原稿の管理と配信ライフサイクル
- AI レスポンスの感情パース
- Body REST API クライアントの管理
- MCP ツールセットの統合

---

## 主要コンポーネント

### 1. main.py
**エントリーポイント**: 初期化と配信の開始・停止を担当。ループの実行は `broadcast_loop.py` に委譲します。配信・録画の開始に失敗した場合は異常終了（Fail-Fast）します。

### 2. broadcast_loop.py
**配信ステートマシン**: `BroadcastPhase` (Enum) と各フェーズハンドラで構成される軽量ステートマシン。

フェーズ:
| フェーズ | 説明 | 遷移先 |
|---------|------|--------|
| `INTRO` | 配信開始の挨拶 | → `NEWS` |
| `NEWS` | コメント優先確認 → ニュース読み上げ | → `NEWS` / `IDLE` |
| `IDLE` | ニュース終了後のコメント待機 | → `IDLE` / `CLOSING` |
| `CLOSING` | 締めの挨拶 → 配信停止 | → 終了 |

各フェーズのハンドラは `BroadcastContext` を受け取り、次の `BroadcastPhase` を返します。

### 3. saint_graph.py
**コアロジック**: Google ADK Agent のラッパー

主要機能:
- Agent の初期化と MCP ツールセット統合
- `process_turn()`: ターン処理と感情パース
- **高レベルメソッド**: `process_intro()`, `process_news_reading()`, `process_news_finished()`, `process_closing()` による配信アクションの抽象化。各フェーズのテンプレート管理もここで行います。
- セッション管理

### 4. news_service.py
**ニュース管理**: Markdown 形式のニュース原稿の読み込み

機能:
- `NEWS_DIR` からの原稿読み込み
- `NewsItem` オブジェクトへの変換
- 配信状態の管理

### 5. news_agent.py
**ニュース収集**: 最新ニュースの自動収集と原稿生成（`scripts/news_collector/`）

機能:
- Google Search を使用した自律的検索
- Markdown 形式への構造化と要約
- ポストプロセス（断り書きの除去等）
- [詳細ドキュメント](../scripts/news-collector.md)

### 6. body_client.py
**Body REST クライアント**: Body への HTTP リクエスト送信

主要メソッド:
- `speak(text, style)`: 発話
- `change_emotion(emotion)`: 表情変更
- `get_comments()`: コメント取得

### 7. prompt_loader.py
**プロンプト管理**: システムプロンプトとキャラクタープロンプトの結合

**ステートレスアーキテクチャの実現**:
- `StorageClient` 経由でプロンプトを読み込み（ローカル / GCS 対応）
- `CHARACTER_NAME` 環境変数でキャラクターを動的に切り替え
- コンテナイメージにキャラクターデータを含めない

読み込み内容:
- `system_prompts/` からのシステムプロンプト読み込み
- `data/mind/{character}/` からのキャラクタープロンプト読み込み
- `mind.json` の読み込み（speaker_id など）

### 8. config.py
**設定管理**: 環境変数の読み込みと定数定義

**ステートレスアーキテクチャの実現**:
- `SecretProvider` 経由で `GOOGLE_API_KEY` を取得（Env / GCP Secret Manager 対応）
- コンテナイメージに機密情報を含めない

主要設定:
- `RUN_MODE`: cli / streamer
- `BODY_URL`: Body サービスの URL
- `WEATHER_MCP_URL`: 天気 MCP サーバーの URL
- `MODEL_NAME`: 使用する Gemini モデル

---

## ディレクトリ構成

```
src/saint_graph/
├── main.py                    # エントリーポイント（初期化・配信開始/停止）
├── broadcast_loop.py          # 配信ステートマシン
├── saint_graph.py             # コアロジック（ADK Agent ラッパー）
├── news_service.py            # ニュース管理
├── body_client.py             # Body クライアント
├── prompt_loader.py           # プロンプト管理
├── config.py                  # 設定管理
└── system_prompts/            # システムプロンプト
    ├── core_instructions.md   # 基本原則
    ├── intro.md               # 挨拶フェーズ
    ├── news_reading.md        # ニュース読み上げ
    ├── news_finished.md       # ニュース終了
    └── closing.md             # 終了フェーズ
```

---

## 関連ドキュメント

- [コアロジック](./core-logic.md) - Agent とターン処理
- [ニュース収集エージェント](../scripts/news-collector.md) - ニュースエージェント（scripts/配下）
- [ニュース配信サービス](./news-delivery.md) - ニュース管理
- [Body クライアント](./body-client.md) - REST クライアント
- [プロンプト設計](./prompts.md) - プロンプトシステム
- [システム概要](../../architecture/overview.md) - 全体アーキテクチャ
