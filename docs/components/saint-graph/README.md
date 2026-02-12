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
**メインループ**: ニュース配信のライフサイクル管理。配信・録画の開始に失敗した場合は異常終了（Fail-Fast）します。

フェーズ:
1. 挨拶（intro）
2. ニュース読み上げ（news_reading）
3. ニュース終了（news_finished）
4. 質疑応答ループ
5. 終了（closing）

### 2. saint_graph.py
**コアロジック**: Google ADK Agent のラッパー

主要機能:
- Agent の初期化と MCP ツールセット統合
- `process_turn()`: ターン処理と感情パース
- セッション管理

### 3. news_service.py
**ニュース管理**: Markdown 形式のニュース原稿の読み込み

機能:
- `NEWS_DIR` からの原稿読み込み
- `NewsItem` オブジェクトへの変換
- 配信状態の管理

### 4. news_agent.py
**ニュース収集**: 最新ニュースの自動収集と原稿生成（`scripts/news_collector/`）

機能:
- Google Search を使用した自律的検索
- Markdown 形式への構造化と要約
- ポストプロセス（断り書きの除去等）
- [詳細ドキュメント](./news-collector.md)

### 5. body_client.py
**Body REST クライアント**: Body への HTTP リクエスト送信

主要メソッド:
- `speak(text, style)`: 発話
- `change_emotion(emotion)`: 表情変更
- `get_comments()`: コメント取得
- `start_recording()` / `stop_recording()`: 録画制御

### 6. prompt_loader.py
**プロンプト管理**: システムプロンプトとキャラクタープロンプトの結合

機能:
- `StorageClient` 経由でプロンプトを読み込み（ローカル / GCS 対応）
- `system_prompts/` からのシステムプロンプト読み込み
- `data/mind/{character}/` からのキャラクタープロンプト読み込み
- `mind.json` の読み込み（speaker_id など）

### 7. config.py
**設定管理**: 環境変数の読み込みと定数定義

主要設定:
- `GOOGLE_API_KEY`: `SecretProvider` 経由で取得（Env / GCP Secret Manager 対応）
- `RUN_MODE`: cli / streamer
- `BODY_URL`: Body サービスの URL
- `WEATHER_MCP_URL`: 天気 MCP サーバーの URL
- `MODEL_NAME`: 使用する Gemini モデル

---

## ディレクトリ構成

```
src/saint_graph/
├── main.py                    # メインループ
├── saint_graph.py             # コアロジック
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
- [ニュース収集](./news-collector.md) - ニュースエージェント
- [ニュース配信](./news-service.md) - ニュース管理
- [Body クライアント](./body-client.md) - REST クライアント
- [プロンプト設計](./prompts.md) - プロンプトシステム
- [システム概要](../../architecture/overview.md) - 全体アーキテクチャ
