# トラブルシューティング

AI Tuber システムでよくある問題とその解決方法をまとめています。

---

## 起動時の問題

### GPU が認識されない

**症状**:
```
Error response from daemon: could not select device driver "" with capabilities: [[gpu]]
```

**原因**: nvidia-docker2 がインストールされていない、または NVIDIA ドライバが正しく設定されていない。

**解決方法**:

```bash
# NVIDIA ドライバのインストール確認
nvidia-smi

# nvidia-docker2 のインストール
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# 動作確認
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

---

### OBS Studio が起動しない

**症状**:
```
Fatal: Unable to open display :99
```

または:

```
X server already running on display :99
```

**原因**: `/tmp/.X99-lock` ファイルが残っている、または Xvfb の起動に失敗している。

**解決方法**:

```bash
# コンテナを停止して再起動
docker compose down
docker compose up obs-studio

# それでも解決しない場合、ボリュームを削除
docker compose down -v
docker compose up --build
```

---

### OBS の自動構成ウィザードが表示される / 起動時にハングする

**症状**:
VNC から確認すると、OBS 起動時に「自動構成ウィザード」や「アップデート確認」のダイアログが表示されて止まっている。ヘッドレス環境ではこれが原因でプロセスが正常に初期化されない。

**原因**: 
`global.ini` や `basic.ini` の初回起動フラグが正しく設定されていない。

**解決方法**:

システム側で以下の設定を `src/body/streamer/obs/config/` 配下の ini ファイルに事前適用しています。もし手動で設定をリセットした場合は再確認してください：

- `global.ini` の `[General]` セクション: `FirstRun=false`
- `basic.ini` の `[General]` セクション: `WizardRunCount=1`

また、内部では最新の OBS 設定（v30.x 対応）をバックポートし、ヘッドレス環境での安定稼働のための厳格な定義を適用しています。

---

### VoiceVox に接続できない

**症状**:
```
ConnectionError: Failed to connect to VoiceVox at http://voicevox:50021
```

**原因**: VoiceVox Engine のヘルスチェックが完了していない。

**解決方法**:

VoiceVox は起動に時間がかかります（最大30秒程度）。以下で状態を確認してください：

```bash
# VoiceVox のログを確認
docker compose logs -f voicevox

# ヘルスチェックの状態を確認
docker compose ps voicevox

# 手動でヘルスチェック
curl http://localhost:50021/version
```

**正常な応答例**:
```json
{"version":"0.14.0"}
```

---

### 環境変数が読み込まれない

**症状**:
```
ERROR: GOOGLE_API_KEY is not set
```

**原因**: `.env` ファイルが存在しない、または形式が間違っている。

**解決方法**:

```bash
# .env ファイルが存在するか確認
ls -la .env

# .env の形式を確認（コメントアウトや空行がないか）
cat .env

# エスケープが必要な特殊文字に注意
# 例: JSON はシングルクォートで囲む
YOUTUBE_CLIENT_SECRET_JSON='{"installed":{...}}'
```

---

## YouTube 配信の問題

### OAuth 認証エラー / トークン更新失敗

**症状**:
```
google.auth.exceptions.RefreshError: ('invalid_grant: Token has been expired or revoked.')
```
または
```
Warning: Scope mismatch during token refresh.
```

**原因**: 
- OAuth トークンの有効期限が切れている、または取り消されている
- リクエストしたスコープが、トークンに含まれるスコープと一致していない（例: `youtube.readonly` を要求したがトークンは `youtube` のみ持っている）

**解決方法**:

1. トークンを再取得してください：
   ```bash
   # 認証ヘルパーを実行
   docker compose exec body-streamer python -m src.body.streamer.scripts.youtube_auth_helper
   ```
2. スコープの一致を確認してください。現在の実装では、トークンに含まれるスコープを優先して使用するように統一されています。
3. `.env` の `YOUTUBE_TOKEN_JSON` が正しい JSON 形式であることを確認してください。

詳細は [YouTube 配信セットアップ](./youtube-setup.md) を参照してください。

---

### activeLiveChatId が見つからない

**症状**:
```
ERROR: No active live chat found. Retrying in 10s...
ERROR: Could not retrieve activeLiveChatId after 10 attempts
```

**原因**: 
- ブロードキャスト作成直後で、YouTube 側でチャットの準備ができていない（反映に数秒〜数十秒かかる場合があります）
- 配信が開始されていない、またはビデオ ID が正しくない

**解決方法**:

1. システムは自動的にリトライします（10回、10秒間隔）。通常、数分以内に解消されます。
2. YouTube Studio で対象の配信が「ライブ配信」として正しく作成されているか確認してください。
3. リトライ上限を調整する必要がある場合は、`src.body.streamer.fetch_comments.py` の `max_retries` を変更してください。

```bash
# Body Streamer のログを確認してリトライ状況を把握
docker compose logs -f body-streamer
```

---

### サブプロセスで認証情報が読み込めない

**症状**:
`body-streamer` は正常に動いているが、`fetch_comments.py`（コメント取得プロセス）が `YOUTUBE_TOKEN_JSON is not set` と出力して終了する。

**原因**: 
`body-streamer` から `fetch_comments.py` を起動する際に、環境変数が正しく引き継がれていない。

**解決方法**:

`src/body/streamer/youtube_comment_adapter.py` の `subprocess.Popen` 呼び出しで、明示的に環境変数を渡しているか確認してください。

```python
# 修正例
self.process = subprocess.Popen(
    ['python', script_path, video_id],
    env=os.environ.copy()  # これが必要
    # ...
)
```

---

### コメントが取得できない

**症状**: 視聴者がコメントを投稿しても AI が反応しない。

**原因**: 
- コメント取得サブプロセスが正常に動作していない
- 配信がプライベートになっている

**解決方法**:

```bash
# コメント取得プロセスのログを確認
docker compose exec body-streamer tail -f /tmp/fetch_comments.log

# プロセスの状態を確認
docker compose exec body-streamer ps aux | grep fetch_comments

# 手動でコメント取得をテスト
docker compose exec body-streamer python -m src.body.streamer.scripts.fetch_comments
```

**注意**: `STREAM_PRIVACY=private` の場合、コメント投稿にはチャンネルのメンバーである必要があります。

---

## 音声・映像の問題

### 音声が再生されない

**症状**: OBS で音声波形が表示されない、または音が聞こえない。

**原因**: 
- 音声ファイルが生成されていない
- OBS のメディアソースが正しく設定されていない
- ボリュームがミュートになっている

**解決方法**:

```bash
# 音声ファイルが生成されているか確認
docker compose exec obs-studio ls -lh /app/shared/voice/

# OBS のログを確認
docker compose logs -f obs-studio

# VNC で OBS を確認
# http://localhost:8080/vnc.html にアクセス
# Voice ソースの設定とボリュームを確認
```

---

### 音声が途切れる・重複する

**症状**: 音声が途中で切れたり、同時に複数の音声が再生される。

**原因**: センテンス順次再生の同期が正しく動作していない。

**解決方法**:

```bash
# Body Streamer のログで再生タイミングを確認
docker compose logs -f body-streamer | grep "play_audio_file"

# WAV ファイルの長さ計算が正しいか確認
docker compose exec body-streamer python -c "
from src.body.streamer.voice import get_wav_duration
duration = get_wav_duration('/app/shared/voice/speech_0001.wav')
print(f'Duration: {duration}s')
"
```

---

### キャラクターの表情が変わらない

**症状**: 感情タグが検出されているのに、OBS の画像が切り替わらない。

**原因**: 
- 画像ファイルが存在しない
- OBS のソース名が一致していない

**解決方法**:

```bash
# 画像ファイルが存在するか確認
ls -lh data/mind/ren/assets/

# OBS シーンの設定を確認（VNC でアクセス）
# 各感情に対応するソース名:
# - ai_neutral
# - ai_joyful
# - ai_fun
# - ai_angry
# - ai_sad

# ログで感情変更リクエストを確認
docker compose logs -f body-streamer | grep "change_emotion"
```

---

## テストの問題

### テストが失敗する (サービス接続)

**症状**:
```
pytest tests/integration/test_rest_body_cli.py FAILED
```

**原因**: Body サービスが起動していない、または接続できない。

**解決方法**:

```bash
# 必要なサービスを起動
docker compose up -d body-cli

# ヘルスチェックが完了するまで待つ
docker compose ps

# テストを再実行
pytest tests/integration/test_rest_body_cli.py -v
```

---

### テストが不安定 (LLM 非決定性)

**症状**:
コードを変更していないのに、`test_weather_scenario` などが時々失敗する。

**原因**: 
LLM（Gemini）の応答は非決定的です。ツールを呼び出す代わりに「いつの天気が知りたいですか？」といった確認の返答をしてしまうことがあり、テストの特定のアサーションに失敗します。

**解決方法**:

1. **アサーションの緩和**: 「特定のツールが呼ばれたか」という厳格な検証だけでなく、「最終的に speak ツールで応答したか」「キャラクター性が維持されているか」など、本質的な動作の検証にシフトします。
2. **リトライの設定**: `pytest-rerunfailures` などを使用して、不安定なテストをリトライするように設定します。
3. **プロンプトの改善**: LLM が迷わないよう、テストデータやシステムプロンプトにより具体的な指示を追加します。

```python
# 修正例: ツール呼び出しがなくても、応答があれば許容する
assert len(speak_calls) > 0
if len(weather_calls) == 0:
    print("Warning: LLM chose to respond without calling weather tool")
```

---

### E2E テストがタイムアウトする

**症状**:
```
TimeoutError: Timed out waiting for service to respond
```

**原因**: すべてのサービスが起動していない、またはヘルスチェックに時間がかかっている。

**解決方法**:

```bash
# すべてのサービスを起動
docker compose up -d

# すべてのサービスが healthy になるまで待つ
docker compose ps

# タイムアウト時間を延長してテスト実行
pytest tests/e2e/ -v --timeout=300
```

---

## パフォーマンスの問題

### 音声生成が遅い

**症状**: VoiceVox での音声生成に時間がかかる。

**原因**: GPU が使用されていない、またはリソース不足。

**解決方法**:

```bash
# GPU 使用状況を確認
nvidia-smi

# VoiceVox が GPU を使用しているか確認
docker compose logs voicevox | grep -i gpu

# メモリ使用量を確認
docker stats
```

**最適化**:
- センテンス単位で並列に音声生成（現在実装済み）
- より高性能な GPU を使用
- VoiceVox の設定で品質を調整

---

### OBS の映像がカクカクする

**症状**: VNC で表示される映像がスムーズでない。

**原因**: 
- ネットワーク帯域の不足
- GPU リソースの不足

**解決方法**:

```bash
# GPU 使用状況を確認
nvidia-smi

# OBS の設定を調整（VNC でアクセス）
# - 解像度を下げる（1920x1080 → 1280x720）
# - フレームレートを下げる（60fps → 30fps）

# docker-compose.yml で shm_size を増やす
# shm_size: '4gb'  # デフォルトは 2gb
```

---

### エンコーダーエラーで録画・配信が失敗する

**症状**:
NVIDIA GPU を搭載しているにもかかわらず、「エンコーダーが見つかりません」といったエラーが発生する。

**原因**: 
OBS 30.x 系へのアップデートに伴い、NVENC 内部名称が `ffmpeg_nvenc` から `nvenc` に変更されたため、古い設定が残っていると不整合が起きる。

**解決方法**:

現在のシステムでは OBS 30.x の最適化を反映済みです。`src/body/streamer/obs/config/basic.ini` 内の `RecEncoder` や `Encoder` 指定が `nvenc` になっていることを確認してください。

```ini
# src/body/streamer/obs/config/basic.ini の例
[Output]
RecEncoder=nvenc
Encoder=nvenc
```

NVIDIA GPU 以外（CPU のみ等）を使用する場合は、この値を `x264` に変更する必要があります。

---

## ログの確認方法

### すべてのサービスのログ

```bash
# リアルタイムでログを表示 (Local Docker)
docker compose logs -f

# 特定のサービスのみ
docker compose logs -f saint-graph
docker compose logs -f body-streamer
docker compose logs -f obs-studio
```

### Cloud Run / Cloud Logging での確認方法

GCP 環境で問題が発生した際は、Logs Explorer で以下のクエリを使用してエラーを確認してください。

- **Saint Graph (Job) のエラー確認**:
  ```text
  resource.type="cloud_run_job" 
  resource.labels.job_name="ai-tuber-saint-graph" 
  severity>=ERROR
```

- **Tools Weather (Service) のエラー確認**:
  ```text
  resource.type="cloud_run_revision" 
  resource.labels.service_name="ai-tuber-tools-weather" 
  severity>=ERROR
```

- **子例外 (ExceptionGroup) の詳細確認**:
  ```text
  resource.type="cloud_run_job"
  textPayload:"ExceptionGroup sub["
```

### ログレベルの調整

```python
# src/saint_graph/main.py
import logging
logging.basicConfig(
    level=logging.DEBUG,  # INFO → DEBUG に変更
    format='%(asctime)s [%(levelname)s] %(message)s'
)
```

---

## クリーンアップ

問題が解決しない場合、システムを完全にリセットしてください。

```bash
# すべてのコンテナとネットワークを削除
docker compose down

# ボリュームも削除（録画ファイルや音声ファイルが消えます）
docker compose down -v

# イメージも削除して再ビルド
docker compose down --rmi all
docker compose up --build
```

---

## よくある質問

### Q: Docker Desktop を使っていますが GPU が使えません

**A**: Docker Desktop では GPU サポートが限定的です。Linux 上で Docker Engine を使用することを推奨します。

---

### Q: M1/M2 Mac で動作しますか？

**A**: VoiceVox と OBS は NVIDIA GPU を必要とするため、ARM ベースの Mac では動作しません。Intel Mac でも GPU サポートが不完全です。

---

### Q: システムが重すぎます

**A**: 以下のサービスを段階的に起動してください：

```bash
# ステップ1: CLI モードで動作確認
docker compose up body-cli saint-graph

# ステップ2: VoiceVox を追加
docker compose up body-streamer saint-graph voicevox

# ステップ3: すべて起動
docker compose up
```

---

## サポート

上記で解決しない場合は、以下の情報を添えて Issue を作成してください：

- OS とバージョン
- Docker と Docker Compose のバージョン
- GPU の種類とドライババージョン
- エラーログ (`docker compose logs` の出力)
- `.env` の設定内容（API キーは伏せる）

---

## 関連ドキュメント

- [セットアップガイド](./setup.md) - 初期セットアップ
- [YouTube 配信セットアップ](./youtube-setup.md) - 配信設定
- [開発者ガイド](./development.md) - 開発環境
- [通信プロトコル](../architecture/communication.md) - API 仕様

---

**最終更新**: 2026-02-02
