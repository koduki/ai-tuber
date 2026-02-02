# API 設計（使用インターフェース）

SaintGraph は以下の外部 API を消費するクライアントとして動作します。Body 機能は REST API、外部ツール（天気など）は MCP プロトコルを使用します。

## REST API インターフェース (Body)
URL (Primary): `http://body-cli:8000` (`MCP_URL` から動的に導出)
URL (Streamer): `http://body-streamer:8000`

### 1. `POST /api/speak`
アバターに発話させるためのアクション。
*   **Request Body:**
    ```json
    {
      "text": "発話させるテキスト内容",
      "style": "発話スタイル（例: neutral, joyful, fun, angry, sad）。デフォルトは neutral。"
    }
    ```
*   **Response:** `{"status": "ok", "result": "..."}`

### 2. `POST /api/change_emotion`
アバターの表情を変更する。
*   **Request Body:**
    ```json
    {
      "emotion": "変更したい感情（例: neutral, joyful, fun, angry, sad）"
    }
    ```
*   **Response:** `{"status": "ok", "result": "..."}`
*   **注意**: 内部的に OBS のソース名（`normal` など）にマッピングされます。API レベルでは `neutral` を使用してください。

### 3. `POST /api/play_audio_file` (v1.2 新規)
事前生成された音声ファイルを再生し、完了まで待機する。センテンス毎の順次再生で使用。
*   **Request Body:**
    ```json
    {
      "file_path": "/app/shared/voice/speech_1234.wav",
      "duration": 5.2
    }
    ```
*   **Response:** `{"status": "ok", "result": "再生完了 (5.2s)"}`
*   **説明**: 
    - `duration` (秒) の間、再生完了を待機してから応答を返す。
    - センテンス毎の音声再生で、前の音声が完了するまで次の音声が始まらないことを保証。

### 4. `GET /api/comments`
直近のユーザーコメントを取得するポーリング用 API。
*   **Response:**
    ```json
    {
      "status": "ok",
      "comments": ["コメント1", "コメント2"]
    }
    ```
    ※ body-streamer の場合は `[{"author": "...", "message": "...", "timestamp": "..."}]` のようにオブジェクトのリストを返します。

### 4. `POST /api/recording/start` (Streamer 固有)
OBS の録画を開始します。

### 5. `POST /api/recording/stop` (Streamer 固有)
OBS の録画を停止します。

---

## MCP サーバーインターフェース (External Tools)
URL (Weather): `http://tools-weather:8001/sse` (`WEATHER_MCP_URL` で設定可能)

### 1. `get_weather` (Observation / 外部 API)
指定された場所の天気情報を取得する。
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

---

## 制約事項
*   **Polling Interval:** `POLL_INTERVAL` (デフォルト: 1.0s)
*   **Timeouts:**
    *   Connect: 30s
    *   Tool Execution: 30s

## 実装戦略

### 構造（マイクロサービス）
各コンポーネントは、サーバー層（Starlette REST API / MCP SSE）とビジネスロジック層（Tools/Logic）を分離した構成をとります。

#### 1. Body/CLI (`src/body/cli/`)
*   `main.py`: **REST サーバー層**。Starlette アプリ定義。
*   `io_adapter.py`: **入出力管理**。
*   `tools.py`: **ロジック層**。

#### 2. Tools/Weather (`src/tools/weather/`)
*   `main.py`: **MCP サーバー層**（FastMCP）。
*   `tools.py`: **ロジック層**。

#### 3. SaintGraph (`src/saint_graph/`)
*   `main.py`: **メインループ**。ニュース配信のライフサイクル管理。
*   `saint_graph.py`: **コアロジック**。Google ADK を使用した LLM 制御と Body 操作。
*   `prompt_loader.py`: **プロンプト管理**。システムプロンプトとキャラクタープロンプトの結合。

### プロンプト設計
プロンプトは、キャラクターに依存しない「システム命令」と、キャラクター固有の「ペルソナ」に分離して定義されます。

#### 1. システムプロンプト (`src/saint_graph/system_prompts/`)
配信のフローや共通の動作ルールを定義します。
*   `core_instructions.md`: 感情タグの付与やツール利用ルールなどの基本原則。
*   `intro.md`, `news_reading.md`, `news_finished.md`, `closing.md`: 各配信フェーズの指示。

#### 2. キャラクタープロンプト (`data/mind/<character_name>/`)
キャラクターの性格、口調、固有の挨拶などを定義します。
*   `persona.md`: キャラクターのアイデンティティと対話スタイルの定義。