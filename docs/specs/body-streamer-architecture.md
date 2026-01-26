# Body Streamer - アーキテクチャ仕様書

**サービス名**: body-streamer  
**役割**: ストリーミング制御ハブ  
**バージョン**: 1.0.0  
**最終更新**: 2026-01-21

---

## 概要

`body-streamer` は、AITuberシステムにおいて「肉体」の役割を担う中核サービスです。
`saint-graph`（脳）からのMCP経由の指示を受け取り、各種デバイス（OBS Studio、VoiceVox Engine、YouTube）を制御します。

### 責任範囲

1. **音声合成**: VoiceVox Engine APIを使用した音声生成
2. **映像制御**: OBS WebSocketを使用した表情切り替え、音声再生
3. **配信連携**: YouTube Live APIを使用したコメント取得（オプション）
4. **MCPサーバー**: `saint-graph`に対してツールAPIを提供

---

## システム構成

### コンポーネント図

```
┌─────────────────────────────────────────┐
│         body-streamer (MCP Server)       │
├─────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │  Tools   │  │  Voice   │  │  OBS   ││
│  │          │  │ Adapter  │  │Adapter ││
│  └──────────┘  └──────────┘  └────────┘│
│  ┌──────────────────────────────────┐  │
│  │      YouTube Adapter (optional)  │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
         ▲              │         │
         │ MCP/SSE      │HTTP     │WebSocket
         │              ▼         ▼
    saint-graph    voicevox   obs-studio
```

### ディレクトリ構造

```
src/body/streamer/
├── __init__.py
├── main.py              # MCPサーバーエントリーポイント
├── tools.py             # MCPツール定義
├── voice.py             # VoiceVox連携
├── obs.py               # OBS Studio連携
├── youtube.py           # YouTube Live連携
├── requirements.txt     # 依存パッケージ
└── Dockerfile           # コンテナビルド定義
```

---

## 依存関係

### Pythonパッケージ (`requirements.txt`)

```
fastapi==0.109.0
uvicorn==0.25.0
mcp==0.9.0
requests==2.31.0
obs-websocket-py==1.0
google-api-python-client==2.111.0
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0
httpx==0.26.0
```

### 外部サービス

| サービス | プロトコル | ポート | 必須 |
|---------|-----------|--------|------|
| voicevox | HTTP API | 50021 | ✅ Yes |
| obs-studio | WebSocket | 4455 | ✅ Yes |
| YouTube Live | REST API | 443 | ❌ Optional |

---

## 環境変数

| 変数名 | デフォルト値 | 説明 |
|--------|------------|------|
| `PORT` | `8000` | MCPサーバーのリスニングポート |
| `VOICEVOX_HOST` | `voicevox` | VoiceVox Engineのホスト名 |
| `VOICEVOX_PORT` | `50021` | VoiceVox Engineのポート |
| `OBS_HOST` | `obs-studio` | OBS WebSocketのホスト名 |
| `OBS_PORT` | `4455` | OBS WebSocketのポート |
| `OBS_PASSWORD` | （空文字列） | OBS WebSocketパスワード |
| `YOUTUBE_API_KEY` | （なし） | YouTube Data API v3のAPIキー |
| `YOUTUBE_LIVE_CHAT_ID` | （なし） | 配信のライブチャットID |
| `YOUTUBE_POLLING_INTERVAL` | `5` | コメント取得間隔（秒） |

---

## MCPツール仕様

### 1. `speak`

**目的**: テキストを音声合成して再生

**引数**:
```python
text: str         # 発話するテキスト
style: str = "normal"  # 発話スタイル (normal, joyful, fun, angry, sad)
```

**戻り値**:
```python
str  # "[speak] '{text}' (style: {style})"
```

**処理フロー**:
1. VoiceVox APIで音声クエリ生成
2. 音声データを合成
3. `/app/shared/audio/speech_{random}.wav` に保存
4. OBS WebSocketで `voice` ソースを更新し、再生リスタートを指示

**エラーハンドリング**:
- VoiceVox接続失敗: ログ出力のみ、エラーを返さない
- OBS接続失敗: ログ出力のみ、音声ファイルは保存済み

---

### 2. `change_emotion`

**目的**: アバターの表情を変更

**引数**:
```python
emotion: str  # 感情名 (neutral, happy, joyful, fun, sad, angry)
```

**戻り値**:
```python
str  # "[change_emotion] {emotion}"
```

**処理フロー**:
1. 感情名をOBSソース名にマッピング
2. すべてのアバターソースを非表示
3. 指定されたソースのみ表示

**感情マッピング**:
```python
EMOTION_MAP = {
    "neutral": "normal",
    "happy": "joyful",
    "joyful": "joyful",
    "fun": "fun",
    "sad": "sad",
    "sorrow": "sad",
    "angry": "angry",
}
```

---

### 3. `start_obs_recording`

**目的**: OBSの録画を開始

**引数**: なし

**戻り値**:
```python
str  # "OBS録画を開始しました。" or エラーメッセージ
```

---

### 4. `stop_obs_recording`

**目的**: OBSの録画を停止

**引数**: なし

**戻り値**:
```python
str  # "OBS録画を停止しました。" or エラーメッセージ
```

---

### 5. `sys_get_comments` (非推奨)

**目的**: YouTube Liveコメントを取得

**引数**: なし

**戻り値**:
```python
str  # JSONフォーマット: "[{'author': 'user1', 'message': 'hello'}]"
```

**注意**:
- YouTube API設定がない場合は空配列を返す
- ポーリングはバックグラウンドスレッドで実行
- 現在は非推奨機能（将来的に別サービスに分離予定）

---

## 共有ボリューム

### `audio_share`

**マウントポイント**: `/app/shared/audio`  
**用途**: 音声ファイルの受け渡し  
**共有先**: `obs-studio` コンテナ

**ファイル命名規則**:
```
speech_{random_4digit}.wav
```

**ライフサイクル**:
- 生成: `voice.py` の `generate_speech()`
- 参照: OBS Studio の `voice` メディアソース
- 削除: 手動削除が必要（自動クリーンアップなし）

---

## Dockerコンテナ仕様

### イメージベース

```dockerfile
FROM python:3.11-slim
```

### ビルドコンテキスト

プロジェクトルート (`.`) をコンテキストとして使用

### ポート公開

- `8002:8000` - MCP Server (SSE endpoint)

### ヘルスチェック

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 5s
  timeout: 2s
  retries: 5
```

### 依存サービス

```yaml
depends_on:
  voicevox:
    condition: service_healthy
  obs-studio:
    condition: service_started
  tools-weather:
    condition: service_healthy
```

---

## ログ仕様

### ログレベル

- `DEBUG`: 詳細な処理フロー
- `INFO`: 主要な処理完了通知
- `WARNING`: 軽微なエラー（処理続行可能）
- `ERROR`: 重大なエラー（処理失敗）

### ログフォーマット

```python
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
```

### 主要なログ出力例

```
2026-01-21 15:47:03,679 - src.body.desktop.obs - INFO - Connecting to OBS at obs-studio:4455
2026-01-21 15:47:03,682 - src.body.desktop.obs - INFO - Connected to OBS WebSocket
2026-01-21 15:47:03,689 - src.body.desktop.obs - INFO - Changed emotion to: joyful (source: joyful)
2026-01-21 15:47:04,596 - src.body.desktop.voice - INFO - Saved audio to /app/shared/audio/speech_4794.wav
2026-01-21 15:47:04,596 - src.body.desktop.obs - INFO - Triggered restart for media source 'voice'
2026-01-21 15:47:04,596 - src.body.desktop.obs - INFO - Refreshed media source 'voice'
```

---

## パフォーマンス要件

### レスポンスタイム

| 操作 | 目標時間 |
|------|---------|
| 音声合成 (30文字) | < 500ms |
| 表情変更 | < 100ms |
| コメント取得 | < 200ms |

### スループット

- 同時音声合成: 1リクエスト（VoiceVoxの制約）
- 表情変更: 制限なし
- コメント取得頻度: 5秒間隔（設定可能）

---

## セキュリティ考慮事項

### 認証

- OBS WebSocket: パスワード認証サポート（`OBS_PASSWORD`）
- YouTube API: APIキー認証

### 機密情報管理

- APIキーは環境変数経由で注入
- `.env` ファイルは `.gitignore` に追加済み
- ログに機密情報を出力しない

### ネットワーク分離

- Docker内部ネットワークのみで通信
- 外部公開はMCPエンドポイント（8002）のみ

## 動作確認・テスト方法

開発中や環境構築後に、各機能が正しく動作するかを以下のコマンドでテストできます。

### 1. 音声合成と再生のテスト (`speak`)

`body-streamer` コンテナ内で直接 `speak` ツールを呼び出し、音声が生成され、OBSで再生されるか確認します。

```bash
docker compose exec -e PYTHONPATH=/app body-streamer python3 -c "
import asyncio
from src.body.desktop.tools import speak
asyncio.run(speak('これはテストメッセージです。正常に聞こえますか？', 'normal'))
"
```

*   **期待結果**:
    *   `body-streamer` のログに `Saved audio to /app/shared/audio/...` と出力される。
    *   VNC画面上の OBS ミキサーの `voice` ソースが反応する。
    *   （音声出力環境がある場合）音声が再生される。

### 2. 表情変更のテスト (`change_emotion`)

アバターの表情（イラスト）が正しく切り替わるか確認します。

```bash
docker compose exec -e PYTHONPATH=/app body-streamer python3 -c "
import asyncio
from src.body.desktop.tools import change_emotion
asyncio.run(change_emotion('happy'))
"
```

*   **期待結果**:
    *   `body-streamer` のログに `Changed emotion to: happy (source: joyful)` と出力される。
    *   VNC画面上の OBS プレビューでイラストが喜びの表情に切り替わる。
    *   その他の表情ソースの表示（👁マーク）がオフになり、指定したソースのみがオンになる。

*   **テスト可能な感情**: `neutral`, `happy`, `fun`, `angry`, `sad`

---

## トラブルシューティング

### よくある問題

#### 1. OBS接続失敗

**症状**:
```
ERROR - Failed to connect to OBS: [Errno 111] Connection refused
```

**原因**: OBS WebSocketサーバーが起動していない

**対処法**:
1. OBSコンテナが起動しているか確認: `docker compose ps`
2. OBSログを確認: `docker compose logs obs-studio`
3. OBSを再起動: `docker compose restart obs-studio`

#### 2. 音声が再生されない

**症状**: 音声ファイルは生成されるが再生されない

**原因**: OBSのメディアソースが正しく設定されていない

**対処法**:
1. VNC (`http://localhost:8080/vnc.html`) でOBSを確認
2. `voice` メディアソースが存在するか確認
3. ソースの設定で `/app/shared/audio/` を指定していることを確認
4. オーディオの詳細プロパティで「モニターと出力」が有効か確認

#### 3. YouTube コメント取得失敗

**症状**: コメントが取得されない

**原因**: APIキーまたはChat IDが未設定

**対処法**:
1. `.env` ファイルを確認
2. `YOUTUBE_API_KEY` と `YOUTUBE_LIVE_CHAT_ID` が設定されているか確認
3. コンテナを再起動: `docker compose restart body-streamer`

---

## 今後の拡張予定

### Short-term (3ヶ月以内)

- [ ] 音声ファイルの自動クリーンアップ
- [ ] 感情の中間状態サポート（フェードイン/アウト）
- [ ] リトライロジックの強化

### Mid-term (6ヶ月以内)

- [ ] YouTube Adapterの分離（別サービス化）
- [ ] Twitch対応
- [ ] 複数キャラクター対応

### Long-term (1年以内)

- [ ] WebRTC対応（リアルタイム双方向通信）
- [ ] AI音声のリアルタイム生成
- [ ] 3D アバター対応

---

## 参考資料

- [VoiceVox Engine API仕様](https://voicevox.github.io/voicevox_engine/)
- [OBS WebSocket Protocol](https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md)
- [YouTube Live Streaming API](https://developers.google.com/youtube/v3/live/docs)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
