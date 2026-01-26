# 外部ツール連携仕様 (MCP & REST)

## 1. 概要
SaintGraph は、外部サービスとの連携に **REST Client (Body操作用)** と **MCP Client (情報取得ツール用)** の 2 つを併用します。

## 2. Body Client (REST)
`src/saint_graph/body_client.py`

アバターの身体的動作（発話、表情、録画、YouTube連携）を制御するための専用クライアントです。確実な実行と同期制御のために HTTP REST API を使用します。

- **通信先**: `http://body-streamer:8000` (または `body-cli:8000`)
- **役割**: システムループ (`main.py`) モジュールからの直接的な指令の実行。

## 3. Tool Client (MCP)
`google.adk.tools.McpToolset`

AI (Gemini) が自発的に使用する外部ツールのためのクライアントです。Model Context Protocol (MCP) を使用し、ツールの動的な発見と実行を行います。

- **通信先**: `config.WEATHER_MCP_URL` (例: `http://tools-weather:8001/sse`)
- **役割**:
  - `get_tools()`: AI が利用可能なツールの一覧を動的に取得。
  - `run_async()`: AI が「ツールを使いたい」と判断した際の命令実行。
- **データ変換**: MCP の JSON Schema を Google Gemini 互換形式に変換して ADK Agent に統合します。

## 4. 呼び出しパターンの棲み分け

| 機能 | 通信方式 | 起動トリガー | 理由 |
|---|---|---|---|
| **発話・感情変更** | REST | **プログラム (Parser)** | エラーを許容せず、常に確実に実行するため |
| **コメント取得** | REST | **プログラム (Loop)** | 定期的なポーリングが必要なため |
| **録画制御** | REST | **プログラム (Setup/Teardown)** | システムの開始・終了と同期させるため |
| **天気予報取得** | MCP | **AI (Autonomous)** | 必要かどうかを AI が判断し、動的に拡張したいため |

## 5. 設定管理
`src/saint_graph/config.py` において、`MCP_URLS` リストから Body 用の URL (REST) と情報取得用の URL (MCP) を識別し、それぞれのクライアントに分配します。
