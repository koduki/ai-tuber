# YouTube コメント取得の修正レポート

> **⚠️ このレポートは古い情報を含んでいます**  
> YouTube認証方式を統一したため、`YOUTUBE_API_KEY` は不要になりました。  
> 最新の情報は [`youtube-auth-unification-report.md`](./youtube-auth-unification-report.md) を参照してください。

## 問題の概要
YouTube Live配信のコメント取得が機能していませんでした。

## 根本原因（初期）
`youtube_comment_adapter.py` でサブプロセス (`fetch_comments.py`) を起動する際、環境変数が渡されていなかったため、`YOUTUBE_API_KEY` が認識されず、コメント取得ができていませんでした。

## 修正内容

### 1. 環境変数の伝播 (`youtube_comment_adapter.py`)
```python
self.process = subprocess.Popen(
    ['python', script_path, video_id], 
    stdout=subprocess.PIPE, 
    stderr=subprocess.PIPE, 
    text=True, 
    bufsize=1,
    env=os.environ.copy()  # ← 追加: 環境変数を子プロセスに渡す
)
```

### 2. エラー監視の強化 (`youtube_comment_adapter.py`)
- **stderrキューの追加**: サブプロセスのエラー出力を監視する専用キューを追加
- **エラーログ出力**: API エラーやその他のエラーを検出し、適切にログ出力

```python
# stderr監視スレッド（エラー検出用）
self.error_thread = threading.Thread(target=self.enqueue_output, args=(self.process.stderr, self.error_q))
self.error_thread.daemon = True
self.error_thread.start()

# get() メソッド内でエラーチェック
while not self.error_q.empty():
    error_line = self.error_q.get_nowait()
    if error_line:
        logger.error(f"YouTube comment subprocess error: {error_line.strip()}")
```

### 3. デバッグログの追加 (`fetch_comments.py`)
- **stderr へのデバッグ出力**: JSON出力 (stdout) と分離して、デバッグ情報を stderr に出力
- **詳細なエラーメッセージ**: API キーが見つからない場合や、API エラーが発生した場合に、より詳細な情報をログ出力

```python
if not api_key:
    error_msg = "YOUTUBE_API_KEY not set"
    print(json.dumps({"error": error_msg}), flush=True)
    print(f"ERROR: {error_msg}", file=sys.stderr, flush=True)  # ← 追加
    return

print(f"DEBUG: Starting comment fetch for video {video_id}", file=sys.stderr, flush=True)
```

## 技術的な知見

### subprocess と環境変数
Python の `subprocess.Popen` は、デフォルトでは親プロセスの環境変数を**継承しません**（`env=None` の場合は継承しますが、明示的に `env` を指定すると上書きされます）。

**ベストプラクティス**:
```python
# 親の環境変数を継承しつつ、追加・上書きしたい場合
env = os.environ.copy()
env['CUSTOM_VAR'] = 'value'
subprocess.Popen(..., env=env)
```

### stdout と stderr の分離
- **stdout**: 構造化データ（JSON）の出力専用
- **stderr**: デバッグログ、エラーメッセージ専用

この分離により、親プロセスは JSON のパースに失敗せず、同時にエラー情報も取得できます。

## 動作確認方法

### 前提条件: YOUTUBE_API_KEY の設定

**重要**: コメント取得には `YOUTUBE_API_KEY` が必要です。これは YouTube OAuth 認証（配信管理用）とは**別**に必要なAPIキーです。

`.env` ファイルに以下を設定してください：
```bash
YOUTUBE_API_KEY=your_youtube_data_api_v3_key_here
```

#### APIキーの取得方法
1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. プロジェクトを選択（または作成）
3. 「APIとサービス」→「認証情報」に移動
4. 「認証情報を作成」→「APIキー」を選択
5. 作成されたAPIキーをコピー
6. （推奨）APIキーの制限で「YouTube Data API v3」のみに制限


### 1. コンテナ再起動
```bash
docker compose down
docker compose up --build -d
```

### 2. ログ確認
```bash
# body-streamer のログでエラーを確認
docker compose logs -f body-streamer | grep -E "(YouTube|comment|ERROR)"

# YouTube comment adapter が正常起動しているか確認
docker compose logs body-streamer | grep "Started YouTube comment adapter"
```

### 3. コメント取得の確認
配信中に以下のAPIを叩いて、コメントが取得できているか確認:
```bash
curl http://localhost:8002/api/streaming/comments
```

期待される出力:
```json
[
  {
    "author": "ユーザー名",
    "message": "コメント内容",
    "timestamp": "2026-02-02T16:00:00Z"
  }
]
```

## 今後の改善提案

1. **リトライロジック**: API エラー時の指数バックオフ実装
2. **ヘルスチェック**: comment adapter の生存確認エンドポイント
3. **テスト**: モックAPI を使った統合テスト

## 更新されたファイル
- `/app/src/body/streamer/youtube_comment_adapter.py`: 環境変数伝播、エラー監視
- `/app/src/body/streamer/fetch_comments.py`: デバッグログ追加
