# MCP Client Specification

## 概要
SaintGraphが外部環境（Body）と通信するためのクライアントモジュール。
Model Context Protocol (MCP) 仕様に基づき、ツールの動的発見と実行を行います。
`src/saint_graph/mcp_client.py` に実装されています。

## Protocol & State Management

### URL Convention
*   **Base URL (SSE):** `config.MCP_URL` (Default: `http://localhost:3000/sse`)
*   **Post URL (RPC):** Base URLの `/sse` を `/messages` に置換して生成します。
    *   例: `http://localhost:3000/sse` -> `http://localhost:3000/messages`

### Connection Flow (`connect()`)
1.  **SSE Handshake:**
    *   `httpx.AsyncClient` で Base URL にGETリクエストを送信。
    *   最初の `data:` 行を受信した時点で接続確立とみなします（簡易実装）。
2.  **Initialize Handshake:**
    *   RPC `initialize` メソッドを送信。
    *   Payload:
        ```json
        {
          "protocolVersion": "2024-11-05",
          "capabilities": {},
          "clientInfo": { "name": "saint-graph", "version": "0.1.0" }
        }
        ```
3.  **Tool Discovery:**
    *   初期化直後に自動的に `tools/list` を呼び出し、内部キャッシュを更新します。

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
    *   JSON-RPC `tools/call` を発行。
    *   **Logging:** `get_comments` ツールの場合のみ、ポーリングによるログ汚染を防ぐためINFOログ出力を抑制します。
*   **Output:**
    *   成功時: `result.content[0].text` を文字列として返す。
    *   失敗時 (`error` フィールド存在時): `Exception` を送出する。

### `list_tools()`
*   RPC `tools/list` を発行し、結果を `self.tools` にキャッシュして返します。
