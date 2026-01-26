# API 設計（使用インターフェース）

SaintGraph はサーバーとして API を公開するのではなく、以下の外部 API を消費するクライアントとして動作します。

## MCP サーバーインターフェース (Body)
URL (Primary): `http://body-cli:8000/sse` (`MCP_URL` で設定可能)
URL (Weather): `http://tools-weather:8001/sse` (`WEATHER_MCP_URL` で設定可能)

### 必須ツール仕様
SaintGraph の対話エンジンは、接続先の MCP サーバーが以下のツールセットを提供していることを前提に動作します。
これらのツール定義は、MCP プロトコルの `tools/list` を通じて動的に取得されますが、そのスキーマは以下のように期待されています。

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

#### 3. `sys_get_comments` (Observation / システム内部用)
直近のユーザーコメントやイベントを取得するポーリング用ツール。
*   **Description:** Retrieve user comments. INTERNAL USE ONLY.
*   **Input Schema:** `{}` (空のオブジェクト)
*   **Output:** `string` (改行区切りのコメントリスト。新規コメントがない場合は "No new comments.")
*   **Usage:** Chat Loop (`main.py`) により定期的に呼び出される。**LLM が自発的に呼ぶことは禁止されています（システム内部用）。**

#### 4. `get_weather` (Observation / 外部 API)
指定された場所の天気情報を取得する。オープンな天気予報 API（Open-Meteo）を使用します。
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
*   **Note:** このツールは専用の `tools-weather` マイクロサービスで提供されます。


## 制約事項
*   **Polling Interval:** `POLL_INTERVAL` (デフォルト: 1.0s)
*   **Timeouts:**
    *   Connect: 30s
    *   Tool Execution: 30s

## 実装戦略

### 推奨構造（マイクロサービス）
各コンポーネントは、サーバー層（FastAPI/SSE）とビジネスロジック層（Tools/Logic）を分離した構成をとります。サーバー層は FastMCP を使って実装します。

#### 1. Body/CLI (`src/body/cli/`)
*   `main.py`: **MCP サーバー層**。FastAPI アプリ定義、SSE エンドポイント、JSON-RPC ルーティング。
*   `io_adapter.py`: **入出力管理**。標準入力スレッドと入出力バッファを管理。
*   `tools.py`: **ロジック層**。`speak`, `get_comments` 等のツール関数の実体。

#### 2. Tools/Weather (`src/tools/weather/`)
*   `main.py`: **MCP サーバー層**。天気予報ツールの公開用 SSE エンドポイント。
*   `tools.py`: **ロジック層**。Open-Meteo API を使用したジオコーディングおよび天気取得ロジック。
*   **HTTP クライアント**: 非同期処理のため、`httpx.AsyncClient` を使用してブロッキングを回避。
*   **ヘルパー関数**: ジオコーディング (`_geocode`)、天気取得 (`_fetch_weather`)、WMO コード変換 (`get_wmo_description`) を個別の関数に分離し、保守性を向上。
*   **WMO コード**: 天気コード（0-95）を日本語の説明文字列にマッピングする定数 `WMO_CODE_MAP` を定義。