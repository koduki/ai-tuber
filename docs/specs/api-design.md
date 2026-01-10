# API Design (Consumed Interfaces)

SaintGraphはサーバーとしてAPIを公開するのではなく、以下の外部APIを消費するクライアントとして動作します。

## MCP Server Interface (Body)
URL: `http://localhost:3000/sse` (Default, Configurable via `MCP_URL`)

### Required Tools Specification
SaintGraphの対話エンジンは、接続先のMCPサーバーが以下のツールセットを提供していることを前提に動作します。
これらのツール定義は、MCPプロトコルの `tools/list` を通じて動的に取得されますが、そのスキーマは以下のように期待されています。

#### 1. `speak` (Action)
アバターに発話させるための主要なアクション。
*   **Description:** Speak text to the audience.
*   **Input Schema:**
    ```json
    {
      "type": "object",
      "properties": {
        "text": { "type": "string", "description": "発話させるテキスト内容" },
        "style": { "type": "string", "description": "発話スタイル（感情やトーンの指定）。省略可能。" }
      },
      "required": ["text"]
    }
    ```

#### 2. `change_emotion` (Action)
アバターの表情を変更する。`speak` と並行して、または独立して呼び出される。
*   **Description:** Change the avatar's facial expression.
*   **Input Schema:**
    ```json
    {
      "type": "object",
      "properties": {
        "emotion": { "type": "string", "description": "変更したい感情（例: happy, sad, angry, surprised, neutral）" }
      },
      "required": ["emotion"]
    }
    ```

#### 3. `get_comments` (Observation)
直近のユーザーコメントやイベントを取得するポーリング用ツール。
*   **Description:** Retrieve user comments.
*   **Input Schema:** `{}` (Empty Object)
*   **Output:** `string` (改行区切りのコメントリスト。新規コメントがない場合は "No new comments.")
*   **Usage:** Chat Loop (`main.py`) により定期的に呼び出される。これだけはLLMが自発的に呼ぶのではなく、システムが観測のために使用する。


## Constraints
*   **Polling Interval:** `POLL_INTERVAL` (Default: 5s)
*   **Timeouts:**
    *   Connect: 30s
    *   Tool Execution: 30s

## Implementation Strategy

### Module Separation
サーバ層（Protocol Handling）とビジネスロジック層（Tool Implementation）を明確に分離します。

### Recommended Structure (Body/CLI)
*   `src/body/cli/main.py`: **MCP Server Layer**. FastAPIアプリ定義、SSEエンドポイント、JSON-RPCルーティングのみを記述。
*   `src/body/cli/tools.py`: **Logic Layer**. 実際のツール関数（`speak`, `get_comments`等）と入出力アダプタを実装。純粋なPython関数として定義し、FastAPIへの依存を持たないようにする。