# API Design (Consumed Interfaces)

SaintGraphはサーバーとしてAPIを公開するのではなく、以下の外部APIを消費するクライアントとして動作します。

## MCP Server Interface (Body)
URL (Primary): `http://body-cli:8000/sse` (Configurable via `MCP_URL`)
URL (Weather): `http://body-weather:8001/sse` (Configurable via `WEATHER_MCP_URL`)

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

#### 4. `get_weather` (Observation / 外部API)
指定された場所の天気情報を取得する。オープンな天気予報API（Open-Meteo）を消費します。
*   **Description:** Retrieve weather information for a specified location and date.
*   **Input Schema:**
    ```json
    {
      "type": "object",
      "properties": {
        "location": { "type": "string", "description": "都市名や地域名（例: Tokyo, Fukuoka）" },
        "date": { "type": "string", "description": "日付（YYYY-MM-DD）または相対日時（today, tomorrow）。省略時は現在・直近の天気。" }
      },
      "required": ["location"]
    }
    ```
*   **Note:** このツールは専用の `body-weather` マイクロサービスで提供されます。


## Constraints
*   **Polling Interval:** `POLL_INTERVAL` (Default: 5s)
*   **Timeouts:**
    *   Connect: 30s
    *   Tool Execution: 30s

## Implementation Strategy

### Recommended Structure (Microservices)
各コンポーネントは、サーバ層（FastAPI/SSE）とビジネスロジック層（Tools/Logic）を分離した構成をとります。サーバ層はFastMCPを使って実装します。

#### 1. Body/CLI (`src/body/cli/`)
*   `main.py`: **MCP Server Layer**. FastAPIアプリ定義、SSEエンドポイント、JSON-RPCルーティング。アバター発話制御を担当。
*   `tools.py`: **Logic Layer**. 実際のツール関数（`speak`, `get_comments`等）と入出力アダプタ（標準入力経由のコメント取得）を実装。

#### 2. Body/Weather (`src/body/weather/`)
*   `main.py`: **MCP Server Layer**. 天気予報ツールの公開用SSEエンドポイント。
*   `tools.py`: **Logic Layer**. Open-Meteo APIを使用したジオコーディングおよび天気取得ロジック。