# YouTube コメント取得 - クイックリファレンス

## ✅ 現在の状態

YouTube Live 配信のリアルタイムコメント取得が**完全に動作中**です！

## 🔑 必要な環境変数

```bash
# OAuth 認証情報（必須）
YOUTUBE_CLIENT_SECRET_JSON='{"installed":{...}}'
YOUTUBE_TOKEN_JSON='{"token":"...", "refresh_token":"...", ...}'

# APIキー（不要！）
# YOUTUBE_API_KEY は削除されました
```

## 🚀 使い方

### 1. 配信開始
```bash
docker compose up --build -d
```

配信が自動的に開始され、ライブチャットが有効になります（最大100秒待機）。

### 2. コメント取得確認
```bash
curl http://localhost:8002/api/streaming/comments | jq .
```

**出力例**:
```json
{
  "status": "ok",
  "comments": [
    {
      "author": "@koduki",
      "message": "そうだよねー",
      "timestamp": "2026-02-02T17:09:56+00:00"
    }
  ]
}
```

### 3. ログ確認
```bash
# OAuth 認証成功を確認
docker compose logs body-streamer | grep "OAuth"

# ライブチャットID取得を確認  
docker compose logs body-streamer | grep "Found live chat ID"

# コメント数を確認
docker compose logs body-streamer | grep "Retrieved.*comments"
```

## 🔍 トラブルシューティング

### コメントが取得できない

**症状**: `{"status":"ok","comments":[]}`

**確認手順**:
1. OAuth 認証が成功しているか
   ```bash
   docker compose logs body-streamer | grep "Successfully authenticated with OAuth"
   ```

2. ライブチャットIDが取得できているか
   ```bash
   docker compose logs body-streamer | grep "Found live chat ID"
   ```

3. YouTube の配信が実際に開始されているか（YouTube Studio で確認）

### "No active live chat found after 10 attempts"

**原因**: ライブチャットの有効化に100秒以上かかっている

**解決策**: `/app/src/body/streamer/fetch_comments.py` の `retry_interval` を増やす
```python
retry_interval = 15  # 10秒 → 15秒に変更
```

### スコープエラー

**エラー**: `google.auth.exceptions.RefreshError: ('invalid_scope: Bad Request')`

**解決策**: トークンを削除して再認証
```bash
# 環境変数から YOUTUBE_TOKEN_JSON を一時削除
docker compose restart body-streamer
# 再認証フローが開始されます
```

## 📚 詳細ドキュメント

完全な技術仕様とアーキテクチャの詳細は以下を参照：
- [YouTube OAuth 統一 - 完全成功レポート](./youtube-oauth-final-success-report.md)

## 📊 システム状態

| 項目 | ステータス |
|------|-----------|
| OAuth 認証 | ✅ 動作中 |
| ライブチャットID取得 | ✅ リトライロジック実装済み |
| コメント取得 | ✅ リアルタイム動作中 |
| APIキー | ✅ 不要（削除済み） |

---

**最終更新**: 2026-02-02  
**ステータス**: ✅ 本番稼働中
