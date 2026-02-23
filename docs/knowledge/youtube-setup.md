# YouTube 配信セットアップガイド

このガイドでは、AI Tuber システムで YouTube Live 配信を行うための認証設定手順を説明します。

---

## 概要

YouTube Live 配信を有効にするには、以下の2つの認証情報が必要です：

1. **OAuth 2.0 クライアント ID** (`YOUTUBE_CLIENT_SECRET_JSON`)
2. **OAuth アクセストークン** (`YOUTUBE_TOKEN_JSON`)

---

## 前提条件

- Google アカウント（YouTube チャンネルを持っている）
- YouTube チャンネルでライブ配信が有効化されている
  - [YouTube Studio](https://studio.youtube.com) → **収益化** → **ライブ配信を有効にする**

---

## 手順 1: OAuth 2.0 クライアント ID の作成

### 1-1. Google Cloud Console でプロジェクトを作成

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. **プロジェクトを作成** をクリック
3. プロジェクト名を入力（例: `ai-tuber-project`）
4. **作成** をクリック

### 1-2. YouTube Data API v3 を有効化

1. **API とサービス** → **ライブラリ** に移動
2. **YouTube Data API v3** を検索
3. **有効にする** をクリック

### 1-3. OAuth 2.0 認証情報を作成

1. **API とサービス** → **認証情報** に移動
2. **認証情報を作成** → **OAuth クライアント ID** を選択
3. **アプリケーションの種類**: **デスクトップアプリ** を選択
4. 名前を入力（例: `AI Tuber Client`）
5. **作成** をクリック

### 1-4. クライアント ID をダウンロード

1. 作成された認証情報の **ダウンロード** ボタンをクリック
2. JSON ファイルがダウンロードされます（例: `client_secret_xxxxx.json`）

### 1-5. JSON の内容を環境変数にコピー

ダウンロードした JSON ファイルの内容を `.env` ファイルに設定します。

```bash
YOUTUBE_CLIENT_SECRET_JSON='{"installed":{"client_id":"123456789.apps.googleusercontent.com","project_id":"ai-tuber-project","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"YOUR_CLIENT_SECRET","redirect_uris":["http://localhost"]}}'
```

> **注**: JSON 全体を一行にして、シングルクォート `'` で囲んでください。

---

## 手順 2: OAuth トークンの取得

OAuth トークンは、実際にユーザーとして YouTube にアクセスするための認証情報です。

### 2-1. 認証スクリプトの準備

プロジェクトには YouTube 認証用のスクリプトが含まれています。

```bash
# 認証スクリプトを実行するための一時コンテナを起動
docker compose run --rm body-streamer python -c "
from body.streamer.youtube_auth import YouTubeOAuth
import json

# OAuth 認証の開始
oauth = YouTubeOAuth(
    client_secret_json=json.loads('YOUR_CLIENT_SECRET_JSON_HERE'),
    token_json=None
)

# 認証 URL を取得
auth_url = oauth.get_authorization_url()
print(f'以下のURLにアクセスして認証してください:')
print(auth_url)
print()
print('認証後に表示されるコードを入力してください:')
code = input('> ')

# トークンを取得
credentials = oauth.exchange_code_for_token(code)
print()
print('以下のトークンを .env ファイルに設定してください:')
print(json.dumps({
    'token': credentials.token,
    'refresh_token': credentials.refresh_token,
    'token_uri': credentials.token_uri,
    'client_id': credentials.client_id,
    'client_secret': credentials.client_secret,
    'scopes': credentials.scopes
}))
"
```

### 2-2. より簡単な方法（推奨）

認証用のヘルパースクリプトを使用して、ブラウザ認証とトークンの取得を簡単に行えます。

```bash
# 認証スクリプトを実行（コンテナが停止していても実行可能）
docker compose run --rm --build body-streamer python -m body.streamer.scripts.youtube_auth_helper
```

このスクリプトは以下を行います：

1. `.env` の `YOUTUBE_CLIENT_SECRET_JSON` から一時的な秘密鍵ファイルを作成
2. 認証用の URL を表示（ブラウザでアクセスして許可）
3. 認証コードを入力
4. **新しいトークン JSON を表示**

### 2-3. トークンを環境変数に設定

スクリプトが最後に出力した `NEW YOUTUBE_TOKEN_JSON` セクションの JSON 文字列（`{...}`）をコピーし、`.env` ファイルに追加します：

```bash
# 例: シングルクォートで囲んで1行で設定
YOUTUBE_TOKEN_JSON='{"token":"ya29.xxxxx","refresh_token":"1//xxxxx", ...}'
```

### 2-4. GCP 環境への反映 (Cloud Run 使用時)

GCP 環境（Cloud Run 等）で配信を行う場合は、取得したトークンを Google Cloud Secret Manager に登録する必要があります。

```powershell
# PowerShell での例
$TOKEN_JSON = 'ここにコピーしたJSONを貼り付け'
$TOKEN_JSON | gcloud secrets versions add youtube-token --data-file=-
```

これにより、次回のジョブ実行時から新しいトークンが使用されます。

---

## 手順 3: 配信設定

`.env` ファイルで配信の詳細を設定します。

```bash
# 配信モードを有効化
STREAMING_MODE=true

# 配信タイトルと説明
STREAM_TITLE="【AI Tuber】本日のニュース配信"
STREAM_DESCRIPTION="AI キャラクターによる自動配信です。"

# 公開設定
STREAM_PRIVACY=private  # private, unlisted, public
```

---

## 手順 4: 配信開始

すべての設定が完了したら、システムを起動します。

```bash
docker compose up --build
```

`STREAMING_MODE=true` の場合、Saint Graph は以下を自動的に実行します：

1. YouTube Live のブロードキャストを作成
2. OBS からストリームを開始
3. リアルタイムでコメントを取得
4. 視聴者の質問に AI が回答

---

## 配信の確認

### YouTube Studio で確認

1. [YouTube Studio](https://studio.youtube.com) にアクセス
2. **配信** → **管理** に移動
3. 作成されたライブ配信が表示されます

### OBS での映像確認

ブラウザで http://localhost:8080/vnc.html にアクセスすると、配信中の映像を確認できます。

---

## トラブルシューティング

### エラー: `Invalid client secret`

- **原因**: `YOUTUBE_CLIENT_SECRET_JSON` が正しく設定されていない
- **対処**: JSON の形式とエスケープが正しいか確認してください

### エラー: `Token has been expired or revoked`

- **原因**: OAuth トークンの有効期限切れ
- **対処**: 手順2を再度実行してトークンを再取得してください

### エラー: `activeLiveChatId not found`

- **原因**: ブロードキャストがまだアクティブになっていない
- **対処**: システムは自動的に10回リトライします（10秒間隔）。数分待ってください。

### ログの確認

```bash
# Body Streamer のログを確認
docker compose logs -f body-streamer

# YouTube コメント取得のログを確認
docker compose exec body-streamer tail -f /tmp/youtube_comment_fetcher.log
```

---

## セキュリティに関する注意

### 認証情報の保護

- `.env` ファイルは **絶対に Git にコミットしない** でください
- `.gitignore` に `.env` が含まれていることを確認してください

### トークンのリフレッシュ

- `refresh_token` が含まれている場合、アクセストークンは自動的に更新されます
- トークンを無効化したい場合は、[Google アカウントのセキュリティ設定](https://myaccount.google.com/permissions) から削除できます

---

## 関連ドキュメント

- [セットアップガイド](./setup.md) - 基本的なセットアップ
- [通信プロトコル](../architecture/communication.md) - YouTube API 仕様
- [データフロー](../architecture/data-flow.md) - YouTube コメント取得フロー
- [トラブルシューティング](./troubleshooting.md) - その他の問題

---

**最終更新**: 2026-02-02
