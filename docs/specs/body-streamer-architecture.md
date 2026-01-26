# Body Streamer - アーキテクチャ仕様書

**サービス名**: body-streamer  
**役割**: ストリーミング制御ハブ（身体）  
**バージョン**: 1.1.0  
**最終更新**: 2026-01-26

---

## 概要

`body-streamer` は、AITuberシステムの「肉体」として、音声合成、映像制御、配信プラットフォームとの連携を一手に引き受けます。
以前のバージョンでは MCP プロトコルを使用していましたが、現在はシンプルで確実な **REST API** インターフェースを提供しています。

### 責任範囲

1. **音声合成**: VoiceVox Engine API を使用した音声生成
2. **映像制御**: OBS WebSocket を使用した表情切り替え、音声再生、録画制御
3. **配信連携**: YouTube Live API を使用したコメント取得
4. **API 提供**: `saint-graph`（脳）に対して RESTful な制御エンドポイントを提供

---

## システム構成

### コンポーネント図

```
┌─────────────────────────────────────────┐
│         body-streamer (REST Server)      │
├─────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │   API    │  │  Voice   │  │  OBS   ││
│  │ Endpoints│  │ Adapter  │  │Adapter ││
│  └──────────┘  └──────────┘  └────────┘│
│  ┌──────────────────────────────────┐  │
│  │      YouTube Adapter (Polling)   │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
          ▲              │         │
          │ HTTP/JSON    │HTTP     │WebSocket
          │              ▼         ▼
     saint-graph    voicevox   obs-studio
```

---

## リソース仕様 (REST API)

通信はすべて `HTTP/1.1`、Content-Type は `application/json` で行われます。

### 1. `POST /api/speak`
テキストを音声合成して OBS で再生します。
- **Request Body**:
  ```json
  { "text": "読み上げる内容", "style": "normal" }
  ```
- **Response**: `{"status": "ok", "result": "..."}`

### 2. `POST /api/change_emotion`
アバターの表情を切り替えます。
- **Request Body**:
  ```json
  { "emotion": "happy" }
  ```
- **Response**: `{"status": "ok", "result": "..."}`

### 3. `GET /api/comments`
取得済みの YouTube コメントリストを返します。
- **Response**:
  ```json
  {
    "status": "ok",
    "comments": [
      { "author": "名前", "message": "内容", "timestamp": "..." }
    ]
  }
  ```

### 4. `POST /api/recording/start`
OBS の録画を開始します。

### 5. `POST /api/recording/stop`
OBS の録画を停止します。

---

## 環境変数 (主要項目)

| 変数名 | デフォルト値 | 説明 |
|--------|------------|------|
| `PORT` | `8000` | RESTサーバーのリスニングポート |
| `VOICEVOX_HOST` | `voicevox` | VoiceVox Engine のホスト名 |
| `OBS_HOST` | `obs-studio` | OBS WebSocket のホスト名 |

---

## 音声生成・再生フロー

1. **音声合成**: `VoiceVox API (/audio_query, /synthesis)` を叩き、WAV バイナリを取得。
2. **永続化**: `/app/shared/audio/speech_{id}.wav` として保存。
3. **OBS 通知**: `SetInputSettings` でメディアソースを新ファイルに更新。
4. **再生開始**: `TriggerMediaInputAction (RESTART)` を送信。

---

## 共有ボリューム

- **`audio_share`**: `/app/shared/audio`
  - `body-streamer` が書き込み、`obs-studio` が読み込みます。
  - キャラクターの「声」を届けるための物理的な通信チャネルとして機能します。

---

## 変更履歴 (v1.0 -> v1.1)
- **MCP から REST への移行**: 以前の MCP サーバー構成を廃止し、よりレイテンシが低くデバッグが容易な REST API に変更。
- **録画制御の追加**: API 経由で OBS の録画状態を制御可能に。
- **Starlette の採用**: 高速な非同期 API サーバーの実装に Starlette を利用。
