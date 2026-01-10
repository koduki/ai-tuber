# MCP Client Specification

## 概要
SaintGraphが外部環境（Body）と通信するためのクライアントモジュール。
Model Context Protocol (MCP) 仕様に基づき、ツールの動的発見と実行を行います。
`src/saint_graph/mcp_client.py` に実装されています。

## Protocol & State Management

### URL Convention
*   **Base URL List (SSE):** `config.MCP_URLS` (List of strings)
    *   Default Primary: `http://body-cli:8000/sse`
    *   Default Weather: `http://body-weather:8001/sse`
*   **Post URL (RPC):** 各 Base URL の `/sse` を `/messages` に置換して生成します。

### Connection Flow (`connect()`)
1.  **Iterative Connection:**
    *   `config.MCP_URLS` に含まれるすべてのURLに対して、並列（`asyncio.gather`）で接続を試みます。
2.  **Internal Client Setup (`SingleMCPClient`):**
    *   各URLに対して個別のセッション管理を行います。
    *   **SSE Handshake:** `httpx.AsyncClient` で Base URL にGETリクエストを送信。
    *   **Initialize Handshake:** RPC `initialize` メソッドを送信。
3.  **Tool Discovery & Aggregation:**
    *   初期化直後に `tools/list` を呼び出し、各サーバが提供するツールを `tool_map` に登録します（Tool Name -> Server Client）。

## Data Conversion Logic

### Schema Mapping (JSON Schema -> Gemini Schema)
MCPのJSON SchemaをGoogle GenAI SDKの `types.Schema` に変換します。
以下の要素を再帰的にサポートします：

*   **Types:** `OBJECT`, `ARRAY`, `STRING`, `INTEGER`, etc.
*   **Properties:** Nested objects via `properties`.
*   **Arrays:** Item types via `items`.
*   **Enums:** `enum` list validation.
*   **Required:** `required` field mapping.

### Tool Conversion (`get_google_genai_tools`)
*   MCPの `tools/list` レスポンスを `types.FunctionDeclaration` のリストに変換します。
*   最終的に `types.Tool` オブジェクトとしてラップして返します。

## Core Methods Specification

### `call_tool(name: str, arguments: dict)`
*   **Input:** ツール名と辞書形式の引数。
*   **Behavior:**
    *   `tool_map` から対象のツールを提供しているサーバ・クライアントを特定します。
    *   特定されたサーバに対して JSON-RPC `tools/call` を発行します。
    *   **Logging:** `get_comments` ツールの場合のみ、ポーリングによるログ汚染を防ぐためINFOログ出力を抑制します。
*   **Output:**
    *   成功時: `result.content[0].text` を文字列として返す。
    *   失敗時 (`error` フィールド存在時): `Exception` を送出する。

### `list_tools()`
*   RPC `tools/list` を発行し、結果を `self.tools` にキャッシュして返します。
