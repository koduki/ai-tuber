# MCP Client Specification

## 概要
SaintGraphが外部環境（Body）と通信するためのクライアントモジュール。
Google ADK の `McpToolset` を使用し、Model Context Protocol (MCP) 仕様に基づいたツールの動的発見と実行を行います。

## Protocol & Connection Management

### URL Convention
*   **Base URL List (SSE):** `config.MCP_URLS` (List of strings)
    *   Default Primary: `http://body-cli:8000/sse`
    *   Default Weather: `http://body-weather:8001/sse`

### Connection Strategy (`McpToolset`)
*   **Initialization:** 各 Base URL に対して `SseConnectionParams(url=url)` を作成し、それを用いて `McpToolset` を初期化します。
*   **Transport:** ADK 内部で SSE (Server-Sent Events) を用いた接続と、JSON-RPC メッセージの送受信が管理されます。
*   **Discovery:** Toolset の初期化時、または `get_tools()` 呼び出し時に、サーバーの提供するツールが自動的にリストアップされます。

## Data Conversion Logic
ADK の `McpToolset` は、以下の変換を内部的に行います。

*   **Schema Conversion:** MCP の JSON Schema 形式から Google Gemini 互換のスキーマ形式への変換。
*   **Tool Wrapping:** 各 MCP ツールを ADK の `Tool` オブジェクトとしてラップ。

## Core Methods Specification

### `get_tools()` (ADK internal)
*   サーバーからツールの一覧を取得し、モデル（Gemini）が理解できる形式で返します。

### `run_async(args, tool_context)` (ADK internal)
*   モデルからの `function_call` に基づき、対象の MCP サーバに対して `tools/call` RPC を発行します。
*   実行結果を文字列（またはオブジェクト）としてモデルに返します。

### Direct Usage in SaintGraph
SaintGraph クラスでは、これらを `google.adk.Agent` に渡すことで統合します。また、`call_tool` メソッドにより特定のツールを手動で呼び出すことが可能です。
