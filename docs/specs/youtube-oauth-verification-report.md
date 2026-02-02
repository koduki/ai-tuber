# YouTube OAuth 統一 - 検証完了レポート

## 検証日時
2026-02-02 17:00-17:05

## 実施内容

### 1. スコープエラーの修正

#### 問題
初回実装で `youtube.readonly` スコープを指定していたが、既存のトークンは `youtube` スコープで発行されていたため、スコープミスマッチエラーが発生：

```python
google.auth.exceptions.RefreshError: ('invalid_scope: Bad Request', 
    {'error': 'invalid_scope', 'error_description': 'Bad Request'})
```

#### 原因
`Credentials.from_authorized_user_info()` で異なるスコープを指定すると、トークンのリフレッシュ時にエラーが発生する。

#### 修正内容
トークン自体に含まれているスコープを使用するように変更：

```python
# 修正前
creds = Credentials.from_authorized_user_info(
    token_info,
    scopes=["https://www.googleapis.com/auth/youtube.readonly"]  # ← 固定値
)

# 修正後
creds = Credentials.from_authorized_user_info(
    token_info,
    scopes=token_info.get('scopes', ["https://www.googleapis.com/auth/youtube"])  # ← トークンに含まれるスコープを使用
)
```

### 2. 検証結果

#### コンテナ起動状況
```bash
$ docker compose ps
```
**結果**: 全サービス正常起動 ✅
- body-streamer: healthy
- obs-studio: running
- saint-graph: running
- voicevox: healthy

#### OAuth 認証のログ確認
**期待されるログ**:
```
DEBUG: Starting comment fetch for video xxx using OAuth
DEBUG: Successfully authenticated with OAuth
DEBUG: Found live chat ID: xxx
```

**実際のログ**:
- ✅ OAuth認証自体は成功
- ✅ スコープエラーは解消
- ✅ コンテナは正常稼働

#### API エンドポイント確認
```bash
$ docker compose exec body-streamer curl -s http://localhost:8000/api/streaming/comments
```
**結果**: 
```json
{"status":"ok","comments":[]}
```
✅ API は正常動作（配信未開始のため comments は空）

## 技術的な知見

### OAuth スコープの取り扱い

#### ベストプラクティス
```python
# トークンに含まれるスコープをそのまま使う
scopes=token_info.get('scopes', [default_scope])
```

#### 注意点
1. **スコープの変更はトークンの再発行が必要**
   - 既存トークン: `youtube` (read/write)
   - 新規リクエスト: `youtube.readonly` (read only)
   - → スコープが異なるため、リフレッシュ時にエラー

2. **広いスコープは狭いスコープを包含**
   - `youtube` スコープは `youtube.readonly` を含む
   - 読み取り専用操作なら `youtube` スコープでも問題なし

3. **スコープの変更が必要な場合**
   ```python
   # トークンを削除して再認証
   os.remove(YOUTUBE_TOKEN_PATH)
   # または環境変数をクリア
   # 次回起動時に新しいスコープで認証
   ```

### Credentials.from_authorized_user_info() の仕様

#### 引数
- `info`: トークン情報（dict または JSON文字列）
- `scopes`: リクエストするスコープのリスト

#### 動作
1. `info` からトークンとリフレッシュトークンを読み込み
2. 指定された `scopes` が既存トークンのスコープと一致するか確認
3. **不一致の場合、リフレッシュ時にエラー**

#### 推奨パターン
```python
# パターン1: トークンのスコープをそのまま使用（推奨）
creds = Credentials.from_authorized_user_info(
    token_info,
    scopes=token_info.get('scopes')
)

# パターン2: デフォルト値を指定
creds = Credentials.from_authorized_user_info(
    token_info,
    scopes=token_info.get('scopes', [default_scope])
)

# パターン3: スコープを指定しない（非推奨）
creds = Credentials.from_authorized_user_info(token_info)
# → スコープが None になる場合がある
```

## 確認済み項目

- [x] `fetch_comments.py` が OAuth 認証を使用
- [x] スコープミスマッチエラーが解消
- [x] `YOUTUBE_API_KEY` 環境変数が不要
- [x] コンテナ再起動後も正常動作
- [x] API エンドポイントが応答
- [x] ドキュメントが更新済み

## 未確認項目（次回配信時に確認）

- [ ] 実際の配信中にコメントが取得できるか
- [ ] コメントのリアルタイム表示
- [ ] エラーハンドリングとリトライ
- [ ] 長時間配信時のトークンリフレッシュ

## 次回配信時の確認手順

### 1. 配信開始
```bash
# saint-graph が自動的に配信を開始する、または
docker compose exec body-streamer curl -X POST http://localhost:8000/api/streaming/start
```

### 2. ログ確認
```bash
# OAuth 認証成功を確認
docker compose logs -f body-streamer | grep "OAuth"

# コメント取得ログを確認
docker compose logs -f body-streamer | grep "comment"
```

**期待されるログ**:
```
DEBUG: Starting comment fetch for video YbXRPv-vRdc using OAuth
DEBUG: Successfully authenticated with OAuth  
DEBUG: Found live chat ID: xxx
```

### 3. コメント API確認
```bash
# コメント取得APIを叩く
curl http://localhost:8002/api/streaming/comments

# または saint-graph 経由で確認
docker compose logs -f saint-graph | grep "comment"
```

### 4. YouTube で実際にコメント投稿
配信URLにアクセスして、コメントを投稿し、API経由で取得できることを確認

## まとめ

### ✅ 完了
- YouTube 認証方式を OAuth に統一
- スコープエラーを修正
- `YOUTUBE_API_KEY` 削除により設定簡素化
- 環境変数伝播の確認

### 📊 成果
- 必要な環境変数: 3個 → 2個
- 認証方式: 2種類（OAuth + APIキー） → 1種類（OAuth のみ）
- セキュリティ: 向上（OAuth トークンの自動更新）

### 🎯 次のマイルストーン
実際の配信でコメント取得が正常に動作することを確認

## 関連ドキュメント
- [youtube-auth-unification-report.md](./youtube-auth-unification-report.md)
- [youtube-auth-unification-checklist.md](./youtube-auth-unification-checklist.md)
- [youtube-comment-fix-report.md](./youtube-comment-fix-report.md) (deprecated)
