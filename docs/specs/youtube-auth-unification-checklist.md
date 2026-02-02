# YouTube 認証統一 - 完了チェックリスト

## ✅ 完了した作業

### 1. コード修正
- [x] `fetch_comments.py`: OAuth認証に移行
  - APIキー方式 → OAuth 認証情報（`Credentials.from_authorized_user_info()`）
  - 環境変数 `YOUTUBE_TOKEN_JSON` を使用
  - スコープ: `https://www.googleapis.com/auth/youtube.readonly`

### 2. 設定ファイル更新
- [x] `.env.example`: `YOUTUBE_API_KEY` を削除
- [x] `docker-compose.yml`: `YOUTUBE_API_KEY` 環境変数を削除
- [x] `youtube_comment_adapter.py`: 環境変数伝播は維持（`YOUTUBE_TOKEN_JSON` を渡す）

### 3. ドキュメント更新
- [x] `youtube-auth-unification-report.md`: 新規作成（統一作業の詳細）
- [x] `youtube-comment-fix-report.md`: 非推奨の注記を追加

## 🎯 結果

### Before（変更前）
```bash
# 必要な環境変数
YOUTUBE_API_KEY=xxx                    # ← APIキー（Google Cloud Consoleで別途取得）
YOUTUBE_CLIENT_SECRET_JSON=xxx         # OAuth認証情報
YOUTUBE_TOKEN_JSON=xxx                 # OAuth トークン
```

### After（変更後）
```bash
# 必要な環境変数
YOUTUBE_CLIENT_SECRET_JSON=xxx         # OAuth認証情報
YOUTUBE_TOKEN_JSON=xxx                 # OAuth トークン（配信管理とコメント取得で共有）
```

## 📊 メリット

| 項目 | 変更前 | 変更後 |
|------|--------|--------|
| 認証方式 | OAuth + APIキー | OAuth のみ |
| 必要な環境変数 | 3つ | 2つ |
| 取得が必要な認証情報 | Google Cloud で2種類 | Google Cloud で1種類 |
| セキュリティ | APIキーは固定 | OAuth トークンは自動更新 |
| APIクォータ | 通常 | 優遇される |

## 🧪 動作確認

### 1. ビルドと起動
```bash
docker compose down
docker compose up --build -d
```

### 2. 環境変数の確認
```bash
# YOUTUBE_API_KEY が無いことを確認
docker compose exec body-streamer printenv | grep YOUTUBE_API_KEY
# (何も表示されなければOK)

# YOUTUBE_TOKEN_JSON が設定されていることを確認
docker compose exec body-streamer printenv | grep YOUTUBE_TOKEN_JSON
# (JSON文字列が表示されればOK)
```

### 3. ログで OAuth 認証成功を確認
```bash
docker compose logs -f body-streamer | grep -E "(OAuth|comment)"
```

**期待されるログ**:
```
DEBUG: Starting comment fetch for video xxx using OAuth
DEBUG: Successfully authenticated with OAuth
DEBUG: Found live chat ID: xxx
```

### 4. コメント取得API の確認
```bash
docker compose exec body-streamer curl -s http://localhost:8000/api/streaming/comments
```

**期待される応答**:
```json
{"status":"ok","comments":[...]}
```

## ⚠️ 注意事項

### OAuth トークンのスコープ
現在の `YOUTUBE_TOKEN_JSON` に含まれるスコープが以下を含んでいることを確認：
- `https://www.googleapis.com/auth/youtube`

このスコープは読み取りと書き込み両方をカバーしているため、コメント取得（読み取り専用）にも使用できます。

### トラブルシューティング

#### エラー: `YOUTUBE_TOKEN_JSON not set`
→ `.env` ファイルに `YOUTUBE_TOKEN_JSON` が設定されているか確認

#### エラー: `Failed to create OAuth credentials`
→ `YOUTUBE_TOKEN_JSON` の JSON フォーマットが正しいか確認
→ 必要なキー（`token`, `refresh_token`, `client_id`, `client_secret`）が含まれているか確認

#### エラー: `insufficient authentication scopes`
→ OAuth トークンに `youtube` スコープが含まれているか確認
→ 再認証が必要な場合は、`YOUTUBE_TOKEN_JSON` を削除して再起動

## 📝 関連ドキュメント

- [youtube-auth-unification-report.md](./youtube-auth-unification-report.md) - 詳細な技術解説
- [youtube-comment-fix-report.md](./youtube-comment-fix-report.md) - 過去の修正履歴（非推奨）
- [body-streamer-architecture.md](./body-streamer-architecture.md) - Body Streamer 全体の仕様

## 🚀 次のステップ

この変更により、YouTube連携がよりシンプルで保守しやすくなりました。
コンテナを再起動して、配信とコメント取得が正常に動作することを確認してください。
