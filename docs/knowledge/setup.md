# セットアップガイド

このガイドでは、AI Tuber システムを動かすための初期設定手順を説明します。

---

## 必要なもの

### システム要件

- **OS**: Linux (Ubuntu 20.04 以上推奨)
- **Docker**: 24.0 以上
- **Docker Compose**: 2.0 以上
- **GPU**: NVIDIA GPU (VoiceVox と OBS で使用)
  - CUDA ドライバ
  - nvidia-docker2

### API キー

- **Google Gemini API キー** (必須)
  - [Google AI Studio](https://aistudio.google.com/) で取得

### 配信をする場合のみ

- **YouTube Data API v3 認証情報** (配信モードの場合)
  - OAuth 2.0 クライアント ID (JSON)
  - OAuth トークン (JSON)

詳細は [YouTube 配信セットアップ](./youtube-setup.md) を参照してください。

---

## インストール手順

### 1. リポジトリのクローン

```bash
git clone https://github.com/koduki/ai-tuber.git
cd ai-tuber
```

### 2. 環境変数の設定

プロジェクトルートに `.env` ファイルを作成します。

#### 録画モード（配信なし）の場合

```bash
# 必須
GOOGLE_API_KEY="your_gemini_api_key_here"

# 動作モード
STREAMING_MODE=false
```

#### 配信モード（YouTube Live）の場合

```bash
# 必須
GOOGLE_API_KEY="your_gemini_api_key_here"

# 動作モード
STREAMING_MODE=true

# YouTube 配信設定
YOUTUBE_CLIENT_SECRET_JSON='{"installed":{"client_id":"...","client_secret":"..."}}'
YOUTUBE_TOKEN_JSON='{"token":"...","refresh_token":"...","token_uri":"..."}'
STREAM_TITLE="本日のライブ配信"
STREAM_DESCRIPTION="AI Tuber による配信です"
STREAM_PRIVACY=private  # private, unlisted, public のいずれか
```

> **注**: YouTube 認証情報の取得方法は [YouTube 配信セットアップ](./youtube-setup.md) を参照してください。

---

## 起動方法

### 本番配信・録画モード（Streamer）

すべてのサービス（OBS、VoiceVox、Saint Graph、Body Streamer）を起動します。

```bash
docker compose up --build
```

起動すると以下のサービスが立ち上がります：

| サービス | URL | 説明 |
|---------|-----|------|
| **OBS Studio** | http://localhost:8080/vnc.html | 映像確認（VNC） |
| **Body Streamer API** | http://localhost:8002 | REST API エンドポイント |
| **VoiceVox Engine** | http://localhost:50021 | 音声合成 API |
| **Weather Tools** | http://localhost:8001 | MCP Server |

### 開発モード（CLI）

OBS や VoiceVox を起動せず、CLI での対話のみを行います。

```bash
docker compose up body-cli saint-graph tools-weather
```

CLI に接続するには：

```bash
docker attach ai-tuber-body-cli-1
```

入力例：
```
こんにちは
```

出力例：
```
[AI (joyful)]: 面を上げよ！わらわこそが紅月れんじゃ！
```

---

## OBS Studio の確認

### VNC での映像確認

ブラウザで http://localhost:8080/vnc.html にアクセスすると、OBS Studio の画面が表示されます。

- **キャラクターの顔**: `ai_neutral.png` がデフォルトで表示
- **音声波形**: メディアソースとして音声ファイルが再生される様子が見える

### OBS シーンの構造

| シーン | 説明 |
|--------|------|
| **Main** | メインシーン（立ち絵 + 音声） |

| ソース | 説明 |
|--------|------|
| **AI Image** | キャラクターの立ち絵（感情に応じて切り替わる） |
| **Voice** | 音声再生用メディアソース |

---

## 録画ファイルの確認

録画された動画ファイルは Docker ボリューム `recordings` に保存されます。

```bash
# ボリュームの場所を確認
docker volume inspect ai-tuber_recordings

# ホストマシンにコピー
docker run --rm -v ai-tuber_recordings:/recordings -v $(pwd):/backup ubuntu cp /recordings/*.mkv /backup/
```

---

## トラブルシューティング

起動時に問題が発生した場合は [トラブルシューティング](./troubleshooting.md) を参照してください。

よくある問題：

- **GPU が認識されない**: nvidia-docker2 がインストールされているか確認
- **OBS が起動しない**: `/tmp/.X99-lock` が残っている可能性があります。コンテナを再起動してください
- **VoiceVox に接続できない**: ヘルスチェックが完了するまで数十秒かかります

---

## 次のステップ

- [YouTube 配信セットアップ](./youtube-setup.md) - YouTube Live 配信を有効化
- [開発者ガイド](./development.md) - コードの編集とテスト実行
- [システム概要](../architecture/overview.md) - アーキテクチャの理解

---

**最終更新**: 2026-02-02
