# 通信プロトコル仕様

AI Tuber システムは **REST API** と **MCP** の2つの通信プロトコルを使い分けます。

---

## REST API インターフェース (Body)

Saint Graph から Body への指令送信に使用します。

### 接続先

- **CLI モード**: `http://body-cli:8000`
- **Streamer モード**: `http://body-streamer:8000`

`RUN_MODE` 環境変数により自動的に切り替わります。

---

## Body REST API エンドポイント

### 1. POST /api/speak

アバターに発話させます。

**Request Body**:
```json
{
  "text": "発話させるテキスト内容",
  "style": "neutral",  // neutral, joyful, fun, angry, sad
  "speaker_id": 46     // オプション。指定された場合は style より優先
}
```

**Response**:
```json
{
  "status": "ok",
  "result": "発話完了"
}
```

**注意**:
- `speaker_id` が指定された場合、`style` は無視されます
- VoiceVox の話者ID を直接指定できます

### 2. POST /api/change_emotion

アバターの表情を変更します。

**Request Body**:
```json
{
  "emotion": "joyful"  // neutral, joyful, fun, angry, sad
}
```

**Response**:
```json
{
  "status": "ok",
  "result": "表情を joyful に変更しました"
}
```

**注意**:
- API レベルでは `neutral` を使用（内部的に OBS のソース名 `normal` にマッピングされます）

### 3. POST /api/play_audio_file

事前生成された音声ファイルを再生し、完了まで待機します（センテンス順次再生用）。

**Request Body**:
```json
{
  "file_path": "/app/shared/voice/speech_1234.wav",
  "duration": 5.2
}
```

**Response**:
```json
{
  "status": "ok",
  "result": "再生完了 (5.2s)"
}
```

**説明**:
- `duration` (秒) の間、再生完了を待機してから応答を返します
- 前の音声が完了するまで次の音声が始まらないことを保証

### 4. GET /api/comments

直近のユーザーコメントを取得します（ポーリング用）。

**Response (CLI モード)**:
```json
{
  "status": "ok",
  "comments": ["コメント1", "コメント2"]
}
```

**Response (Streamer モード)**:
```json
{
  "status": "ok",
  "comments": [
    {
      "author": "@username",
      "message": "コメント内容",
      "timestamp": "2026-02-02T17:00:00+00:00"
    }
  ]
}
```

### 5. POST /api/recording/start (Streamer 固有)

OBS の録画を開始します。

**Response**:
```json
{
  "status": "ok",
  "result": "録画を開始しました"
}
```

### 6. POST /api/recording/stop (Streamer 固有)

OBS の録画を停止します。

**Response**:
```json
{
  "status": "ok",
  "result": "録画を停止しました"
}
```

### 7. POST /api/streaming/start (Streamer 固有)

YouTube Live 配信を作成・開始します。

**Request Body**:
```json
{
  "title": "配信タイトル",
  "description": "配信の説明",
  "scheduled_start_time": "2024-12-31T00:00:00.000Z",
  "thumbnail_path": "/path/to/thumbnail.png",  // オプション
  "privacy_status": "private"  // private, unlisted, public
}
```

**Response**:
```json
{
  "status": "ok",
  "result": "YouTube Live配信を開始しました。ブロードキャストID: xxxxx"
}
```

### 8. POST /api/streaming/stop (Streamer 固有)

YouTube Live 配信を停止します。

**Response**:
```json
{
  "status": "ok",
  "result": "YouTube Live配信を停止しました"
}
```

### 9. GET /api/streaming/comments (Streamer 固有)

YouTube Live 配信のリアルタイムチャットコメントを取得します。

**Response**:
```json
{
  "status": "ok",
  "comments": [
    {
      "author": "@username",
      "message": "コメント内容",
      "timestamp": "2026-02-02T17:00:00+00:00"
    }
  ]
}
```

---

## MCP インターフェース (Tools)

AI が自律的に呼び出す外部ツールに使用します。

### 接続先

- **Weather Tool**: `http://tools-weather:8001/sse`

環境変数 `MCP_URL` で設定可能です。

---

## Weather MCP Server

### get_weather

指定された場所の天気情報を取得します。

**Description**: Retrieve weather information for a specified location and date.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "location": {
      "type": "string",
      "description": "都市名や地域名（例: Tokyo, Fukuoka）"
    },
    "date": {
      "type": "string",
      "description": "日付（YYYY-MM-DD）または相対日時（today, tomorrow）。省略時は現在・直近の天気。"
    }
  },
  "required": ["location"]
}
```

**呼び出し例**:
```python
# AI が自律的にツールとして呼び出し
result = await agent.run("東京の明日の天気を教えて")
# → AI が get_weather(location="Tokyo", date="tomorrow") を使用
```

---

## 呼び出しパターンの棲み分け

| 機能 | 通信方式 | 起動トリガー | 理由 |
|---|---|---|---|
| **発話・感情変更** | REST | **プログラム（Parser）** | エラーを許容せず、常に確実に実行するため |
| **コメント取得** | REST | **プログラム（Loop）** | 定期的なポーリングが必要なため |
| **録画・配信制御** | REST | **プログラム（Setup/Teardown）** | システムの開始・終了と同期させるため |
| **天気予報取得** | MCP | **AI（Autonomous）** | 必要かどうかを AI が判断し、動的に拡張したいため |

---

## 環境変数

### Saint Graph 設定

| 変数名 | デフォルト値 | 説明 |
|--------|-------------|------|
| `RUN_MODE` | `cli` | 動作モード（`cli` または `streamer`） |
| `BODY_URL` | (自動設定) | Body サービスの URL（RUN_MODE により決定） |
| `MCP_URL` | `http://tools-weather:8001/sse` | MCP サーバーの URL |
| `GOOGLE_API_KEY` | (必須) | Google Gemini API キー |
| `MODEL_NAME` | `gemini-2.5-flash-lite` | 使用する Gemini モデル |
| `ADK_TELEMETRY` | `false` | Google ADK テレメトリの有効化 |
| `NEWS_DIR` | `/app/data/news` | ニュース原稿ディレクトリ |
| `MAX_WAIT_CYCLES` | `30` | ニュース終了後の沈黙タイムアウト（秒） |

### Body 設定

| 変数名 | デフォルト値 | 説明 |
|--------|-------------|------|
| `PORT` | `8000` (CLI) / `8002` (Streamer) | REST サーバーのポート |
| `VOICEVOX_HOST` | `voicevox` | VoiceVox Engine のホスト名 |
| `OBS_HOST` | `obs-studio` | OBS WebSocket のホスト名 |
| `YOUTUBE_CLIENT_SECRET_JSON` | - | OAuth 認証情報の JSON 文字列 |
| `YOUTUBE_TOKEN_JSON` | - | OAuth トークンの JSON 文字列 |

---

## タイムアウトと制約

### Saint Graph

- **Polling Interval**: `1.0s` (コメント取得の間隔)
- **Connect Timeout**: `30s`
- **Tool Execution Timeout**: `30s`

### Body

- **OBS WebSocket 接続リトライ**: 最大5回、指数バックオフ（2秒 → 4秒 → 8秒...）
- **YouTube Live Chat ID取得リトライ**: 最大10回、10秒間隔

---

## 関連ドキュメント

- [システム概要](./overview.md) - 全体アーキテクチャ
- [Saint Graph - Body Client](../components/saint-graph/body-client.md) - REST クライアント実装
- [Body](../components/body/README.md) - REST サーバー実装
- [Body Tools - Weather](../components/body/tools/weather.md) - MCP サーバー実装
