---
description: AI Newscaster アプリケーション実装仕様書
---

# アプリケーション実装仕様書: Saint Graph AI Newscaster

## 1. 概要
**Saint Graph AI Newscaster** は、LLM (Gemini) によって駆動される、キャラクター主導の自動配信システムです。
Markdown ファイルからニュース原稿を読み込み、ペルソナに基づいた解説を加え、OBS を通じて配信を行います。

## 2. アーキテクチャ (Hybrid REST/MCP)
システムは役割に応じて通信プロトコルを使い分けるハイブリッド構成を採用しています。

- **`saint-graph`**: コアロジック（魂/脳）。
  - **REST Client**: `body-cli` または `body-streamer` に対して、発話・感情変更・コメント取得・録画制御などの「身体操作」を明示的に要求します。
  - **MCP Client**: 天気予報などの「外部ツール」を ADK Toolset 経由で探索・実行します。
  - **Output Parser**: AI の生成テキストから感情タグ `[emotion: type]` を抽出し、身体への指示に変換します。

- **`body-streamer`**: ストリーミング制御（肉体）。
  - **REST Server**: `saint-graph` からの HTTP リクエストを受け、OBS や VoiceVox を制御します。
  - **Adapter**: VoiceVox, OBS WebSocket, YouTube Live 等の外部サービスを抽象化します。

- **`tools-weather`**: 外部ツール（環境）。
  - **MCP Server**: 天気データを提供します。AI が必要に応じて自律的に呼び出します。

## 3. 主要コンポーネント

### 3.1 News Service (`src/saint_graph/news_service.py`)
- **機能**: `news_script.md` を解析して `NewsItem` オブジェクトに変換します。
- **フォーマット**: `## Title` ヘッダーを持つ Markdown。

### 3.2 Body Client (`src/saint_graph/body_client.py`)
- **機能**: Body サービス (CLI/Streamer) への HTTP リクエストをカプセル化します。
- **メソッド**: `speak()`, `change_emotion()`, `get_comments()`, `start_recording()`, `stop_recording()`。

### 3.3 Saint Graph Agent (`src/saint_graph/saint_graph.py`)
- **ADK 統合**: `google.adk.Agent` をラップし、MCP ツールセットを統合。
- **ターン処理 (`process_turn`)** (v1.2 更新):
  1. AI にユーザー入力を送り、ストリーミングレスポンスを受け取ります。
  2. 生成されたテキスト全体をセンテンス単位（`。！？.!?`）で分割します。
  3. 各センテンスから `[emotion: type]` タグを抽出し、感情と発話内容を確定します。
  4. センテンスごとに以下を順次実行:
     - 感情が変わっている場合: `BodyClient.change_emotion()` を実行
     - 音声生成と再生: `BodyClient.speak()` を実行（再生完了まで待機）
  5. 全センテンスの再生が完了してから次のターンへ進みます。

### 3.4 システムプロンプト (`src/saint_graph/system_prompts/`)
- **`core_instructions.md`**:
  - レスポンスの先頭に必ず `[emotion: <type>]` を付けるよう指示。
  - 天気などの外部情報取得は `get_weather` ツールを使うよう指示。
  - 直接的な `speak` 工具の呼び出し指示を廃止し、自然なテキスト生成を優先。

## 4. 実行シーケンス

1. **初期化**: `BodyClient` を作成し、外部 MCP サーバーと接続。録画を開始。
2. **メインループ**:
   - `get_comments()` API を叩き、未処理のコメントがあれば AI に渡す。
   - 次のニュース項目があれば AI に読み上げ指示を出す。
   - AI からの返答（例: `[emotion: joyful] 皆の衆、おはのじゃ！`）を受け取る。
   - `[emotion: joyful]` をパースし、Body API で感情を `joyful` に、発話をテキストに設定。
3. **終了**: 一定時間の沈黙後、クロージング挨拶を行い、録画を停止して終了。

## 5. 設計の意図
- **確実性の向上**: AI にツール呼び出しを強制するのではなく、生成されたテキストから感情を抽出することで、発話忘れやツール呼び出しの失敗を防ぎます。
- **疎結合思考**: 「身体」の操作は標準的な REST API とし、AI が「知恵」として使う外部ツールのみを MCP とすることで、システムの複雑さを分離しています。
