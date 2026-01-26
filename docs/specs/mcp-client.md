# MCP クライアント仕様書

## 概要
SaintGraph が外部環境（Body）と通信するためのクライアントモジュール。
Google ADK の `McpToolset` を使用し、Model Context Protocol (MCP) 仕様に基づいたツールの動的発見と実行を行います。

## プロトコル & 接続管理

### URL コンベンション
*   **Base URL リスト (SSE):** `config.MCP_URLS` (文字列のリスト)
    *   デフォルト Primary: `http://body-cli:8000/sse`
    *   デフォルト Weather: `http://tools-weather:8001/sse`

### 接続戦略 (`McpToolset`)
*   **初期化:** 各 Base URL に対して `SseConnectionParams(url=url)` を作成し、それを用いて `McpToolset` を初期化します。
*   **トランスポート:** ADK 内部で SSE (Server-Sent Events) を用いた接続と、JSON-RPC メッセージの送受信が管理されます。
*   **ディスカバリー:** Toolset の初期化時、または `get_tools()` 呼び出し時に、サーバーの提供するツールが自動的にリストアップされます。

## データ変換ロジック
ADK の `McpToolset` は、以下の変換を内部的に行います。

*   **スキーマ変換:** MCP の JSON Schema 形式から Google Gemini 互換のスキーマ形式への変換。
*   **ツールラッピング:** 各 MCP ツールを ADK の `Tool` オブジェクトとしてラップ。

## 主要メソッド仕様

### `get_tools()` (ADK 内部用)
*   サーバーからツールの一覧を取得し、モデル（Gemini）が理解できる形式で返します。

### `run_async(args, tool_context)` (ADK 内部用)
*   モデルからの `function_call` に基づき、対象の MCP サーバーに対して `tools/call` RPC を発行します。
*   実行結果を文字列（またはオブジェクト）としてモデルに返します。

### SaintGraph における直接利用
SaintGraph クラスでは、これらを `google.adk.Agent` に渡すことで統合します。また、`call_tool` メソッドにより、特定のツールを手動で呼び出すことが可能です。
