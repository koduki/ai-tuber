# YouTube 認証方式の統一レポート

## 実施日
2026-02-02

## 背景
YouTube API との連携で2種類の認証方式が混在していました：
1. **OAuth 2.0** - 配信作成・管理用（`youtube_live_adapter.py`）
2. **APIキー** - コメント取得用（`fetch_comments.py`）

この混在により、以下の問題がありました：
- 環境変数の管理が複雑
- 認証エラーのデバッグが困難
- APIキーの別途取得が必要

## 実施内容

### 1. `fetch_comments.py` の OAuth 化

#### 変更前（APIキー方式）
```python
api_key = os.getenv("YOUTUBE_API_KEY", "")
if not api_key:
    print(json.dumps({"error": "YOUTUBE_API_KEY not set"}), flush=True)
    return

youtube = build('youtube', 'v3', developerKey=api_key)
```

#### 変更後（OAuth方式）
```python
youtube_token_json = os.getenv("YOUTUBE_TOKEN_JSON", "")
if not youtube_token_json:
    print(json.dumps({"error": "YOUTUBE_TOKEN_JSON not set"}), flush=True)
    return

token_info = json.loads(youtube_token_json)
creds = Credentials.from_authorized_user_info(
    token_info,
    scopes=["https://www.googleapis.com/auth/youtube.readonly"]
)

youtube = build('youtube', 'v3', credentials=creds)
```

**ポイント**:
- `Credentials.from_authorized_user_info()` で JSON 文字列から認証情報を復元
- スコープは `youtube.readonly` で十分（読み取り専用）
- 配信管理（`youtube_live_adapter.py`）と同じ OAuth トークンを共有

### 2. 環境変数の削除

以下のファイルから `YOUTUBE_API_KEY` を削除：

#### `.env.example`
```diff
-# YouTube Live API (Optional - for comment fetching)
-YOUTUBE_API_KEY=your_youtube_api_key_here
+# YouTube Live Chat ID (Optional - can be auto-detected from broadcast)
 YOUTUBE_LIVE_CHAT_ID=your_live_chat_id_here
```

#### `docker-compose.yml`
```diff
     environment:
       ...
-      - YOUTUBE_API_KEY=${YOUTUBE_API_KEY:-}
       - YOUTUBE_LIVE_CHAT_ID=${YOUTUBE_LIVE_CHAT_ID:-}
       ...
```

### 3. スコープの適切化

| 機能 | 使用スコープ | 用途 |
|------|------------|------|
| 配信作成・管理 | `https://www.googleapis.com/auth/youtube` | 書き込み権限（配信作成、設定変更） |
| コメント取得 | `https://www.googleapis.com/auth/youtube.readonly` | 読み取り専用 |

**注意**: 現在は両方の機能で広い権限（`youtube`）のトークンを使用していますが、将来的には最小権限の原則で分離することも可能です。

## メリット

### 1. 設定の簡素化
- ✅ 必要な環境変数が減った（`YOUTUBE_API_KEY` 不要）
- ✅ 認証方式が統一された（すべて OAuth）
- ✅ `.env` ファイルの管理が簡単に

### 2. セキュリティの向上
- ✅ APIキーよりOAuthの方がセキュア（トークンの定期更新、スコープ制限）
- ✅ リフレッシュトークンによる自動更新

### 3. APIレート制限の緩和
- ✅ OAuth 認証の方が API クォータが優遇される
- ✅ プロジェクト単位での管理が容易

## 技術的な知見

### OAuth トークンの共有
同じ YouTube OAuth トークンを複数の用途で使用できます：
- **配信管理** (`youtube_live_adapter.py`): 書き込み権限が必要
- **コメント取得** (`fetch_comments.py`): 読み取り権限のみ

トークンに含まれるスコープ（権限）が十分であれば、両方で同じトークンを使用可能です。

### Credentials.from_authorized_user_info() の利点
- JSON文字列から直接 Credentials オブジェクトを作成可能
- ファイルI/Oが不要（環境変数から直接読み込める）
- コンテナ環境での柔軟な設定が可能

## 動作確認方法

### 1. 環境変数の確認
OAuth 認証情報が設定されているか確認：
```bash
docker compose exec body-streamer printenv | grep YOUTUBE_TOKEN_JSON
```

### 2. コメント取得のテスト
配信開始後、コメント取得が動作しているか確認：
```bash
# エラーログの確認
docker compose logs -f body-streamer | grep -E "(comment|OAuth|ERROR)"

# コメント取得のAPI確認
docker compose exec body-streamer curl -s http://localhost:8000/api/streaming/comments
```

### 3. 期待される動作
- ❌ **以前**: `ERROR: YOUTUBE_API_KEY not set`
- ✅ **現在**: `DEBUG: Successfully authenticated with OAuth`

## 今後の改善提案

### 1. スコープの最小化
配信管理とコメント取得で別々のOAuthトークンを使用し、スコープを最小限に：
```python
# 配信管理用
scopes_manage = ["https://www.googleapis.com/auth/youtube"]

# コメント取得用（読み取り専用）
scopes_readonly = ["https://www.googleapis.com/auth/youtube.readonly"]
```

### 2. トークン更新の自動化
リフレッシュトークンを使った自動更新をより堅牢に：
```python
if creds and creds.expired and creds.refresh_token:
    logger.info("Refreshing OAuth token...")
    creds.refresh(Request())
    # 更新後のトークンを保存
```

### 3. エラーハンドリングの強化
OAuth エラーの詳細なログとリトライロジック

## 更新されたファイル
- `/app/src/body/streamer/fetch_comments.py`: OAuth認証に変更
- `/app/.env.example`: YOUTUBE_API_KEY を削除
- `/app/docker-compose.yml`: YOUTUBE_API_KEY を削除
- `/app/docs/specs/youtube-auth-unification-report.md`: 本ドキュメント

## 参考リンク
- [Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)
- [YouTube Data API v3 - Authentication](https://developers.google.com/youtube/v3/guides/authentication)
- [Python Google Auth Library](https://google-auth.readthedocs.io/)
