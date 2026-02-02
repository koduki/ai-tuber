# YouTube Live Streaming Integration

このドキュメントでは、AI TuberシステムにおけるYouTube Live配信機能の使い方を説明します。

## 概要

システムには2つのモードがあります:

1. **録画モード** (デフォルト): OBSで動画を録画
2. **配信モード**: YouTube Liveにストリーミング配信

## セットアップ

### 1. 環境変数の設定

`.env`ファイルに以下を追加:

```bash
# 配信モードを有効化 (デフォルトはfalse)
STREAMING_MODE=false

# YouTube OAuth認証情報のパス (配信モード時に必要)
YOUTUBE_CLIENT_SECRET_PATH=/secret/google_client_secret.json
YOUTUBE_TOKEN_PATH=/secret/yt_token.json

# YouTube Data API v3キー (コメント取得用)
YOUTUBE_API_KEY=your_youtube_api_key_here
```

### 2. YouTube OAuth認証情報の取得

配信モードを使用するには、Google Cloud ConsoleからOAuth 2.0認証情報を取得する必要があります:

1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. プロジェクトを作成または選択
3. [YouTube Data API v3](https://console.cloud.google.com/apis/library/youtube.googleapis.com)を有効化
4. 「認証情報」→「OAuth 2.0クライアントID」を作成
5. アプリケーションの種類: デスクトップアプリ
6. JSONファイルをダウンロードし、`/secret/google_client_secret.json`として保存（または環境変数 `YOUTUBE_CLIENT_SECRET_JSON` に内容を貼り付け）

### シークレット管理 (Docker/環境変数方式)

マウントによるファイル格納の代わりに、Dockerの環境変数としてJSON内容を直接渡すことも可能です。この場合、起動時にコンテナ内のファイルとして自動出力されます。

`.env` または Docker Compose の `environment` セクションに以下を設定:

```bash
# JSONの内容をシングルクォートで囲んで設定してください
YOUTUBE_CLIENT_SECRET_JSON='{"installed":{"client_id":"...","...":"..."}}'

# 初回認証後のトークンも同様に設定可能です
YOUTUBE_TOKEN_JSON='{"token":"...","refresh_token":"...","...":"..."}'
```

設定されている場合、システムは自動的に `YOUTUBE_CLIENT_SECRET_PATH` 等で指定されたパス（デフォルト: `/secret/google_client_secret.json`）にファイルを書き出し、それを使用して認証を行います。

### 3. 初回認証と自動実行

本システムは、`docker-compose up` で起動すると `saint-graph` が自動的にYouTube Liveの配信開始を試行します。
初めて実行する場合や、トークンが更新されていない場合は以下の手順で認証を行います。

#### 認証の手順:

1. `docker-compose up` でシステムを起動
2. コンテナのログに `AUTHORIZATION REQUIRED FOR YOUTUBE LIVE` というメッセージとURLが表示されます
3. ブラウザでURLを開き、Googleアカウントでログインして「認証コード」を取得します
4. ターミナルで `docker attach <body-streamerのコンテナID>` を実行し、認証コードを入力してエンターを押します
5. 認証が成功すると `/secret/yt_token.json` が作成され、次回以降は自動で配信が開始されるようになります

> [!TIP]
> **完全に自動化する場合**: 一度生成された `yt_token.json` の内容を環境変数 `YOUTUBE_TOKEN_JSON` に設定しておけば、初回認証のステップも不要になり、`docker-compose up` だけで即座に配信が開始されます。

### 4. 配信の制御

`saint-graph` の環境変数で配信内容をカスタマイズできます：

- `STREAM_TITLE`: 配信タイトル
- `STREAM_DESCRIPTION`: 配信説明
- `STREAM_PRIVACY`: 公開設定 (`public`, `unlisted`, `private`)

## API エンドポイント

### 配信開始

```bash
POST /api/streaming/start
```

リクエストボディ:
```json
{
  "title": "配信タイトル",
  "description": "配信の説明",
  "scheduled_start_time": "2024-12-31T00:00:00.000Z",
  "thumbnail_path": "/path/to/thumbnail.png",  // オプション
  "privacy_status": "private"  // private, unlisted, public
}
```

レスポンス:
```json
{
  "status": "ok",
  "result": "YouTube Live配信を開始しました。ブロードキャストID: xxxxx"
}
```

### 配信停止

```bash
POST /api/streaming/stop
```

レスポンス:
```json
{
  "status": "ok",
  "result": "YouTube Live配信を停止しました。"
}
```

### 配信コメント取得

```bash
GET /api/streaming/comments
```

レスポンス:
```json
{
  "status": "ok",
  "comments": [
    {
      "author": "ユーザー名",
      "message": "コメント内容",
      "timestamp": "2024-12-31T00:00:00.000Z"
    }
  ]
}
```

## 録画モード (既存の機能)

録画モードでは、以下のエンドポイントを使用します:

### 録画開始
```bash
POST /api/recording/start
```

### 録画停止
```bash
POST /api/recording/stop
```

### コメント取得 (YouTube Live Chat IDが設定されている場合)
```bash
GET /api/comments
```

## 実装の詳細

### アーキテクチャ

```
┌─────────────────────┐
│  main.py            │  API エンドポイント
│  (Starlette REST)   │
└──────────┬──────────┘
           │
           ├── start_streaming_api() → tools.start_streaming()
           ├── stop_streaming_api()  → tools.stop_streaming()
           └── get_streaming_comments_api() → tools.get_streaming_comments()
                      │
                      ├── YoutubeLiveAdapter
                      │   ├── authenticate_youtube()
                      │   ├── create_live()
                      │   └── stop_live()
                      │
                      ├── YouTubeCommentAdapter
                      │   ├── get() コメント取得
                      │   └── subprocess: fetch_comments.py
                      │
                      └── OBS Adapter
                          ├── start_streaming(stream_key)
                          └── stop_streaming()
```

### ファイル構成

- `youtube_live_adapter.py`: YouTube Live API連携
- `youtube_comment_adapter.py`: サブプロセスでコメント取得
- `fetch_comments.py`: YouTube Live Chatコメント取得スクリプト
- `obs.py`: OBS WebSocket制御 (streaming methods追加)
- `tools.py`: 配信ツール関数
- `main.py`: REST APIエンドポイント

## トラブルシューティング

### 認証エラー

```
Error: invalid_grant
```

→ `yt_token.json`を削除して再認証してください

### OBS接続エラー

```
OBSストリーミングの開始に失敗しました。
```

→ OBS Studioが起動しており、WebSocketが有効になっていることを確認してください

### YouTube API エラー

```
quotaExceeded
```

→ YouTube Data API v3の1日のクォータ制限に達しました。翌日まで待つか、Google Cloud Consoleでクォータを確認してください

## 参考リンク

- [YouTube Data API v3](https://developers.google.com/youtube/v3)
- [YouTube Live Streaming API](https://developers.google.com/youtube/v3/live/docs)
- [OBS WebSocket Protocol](https://github.com/obsproject/obs-websocket)
