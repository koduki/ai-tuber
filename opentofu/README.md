
このディレクトリには、AI Tuber システムを Google Cloud Platform (GCP) にデプロイするための OpenTofu 設定と手順が含まれています。

## アーキテクチャ概要

- **Cloud Workflows**: 配信パイプライン全体のオーケストレーション（条件分岐・リトライ制御）
- **Cloud Run Service**: 
  - Tools Weather (MCP サーバー、ステートレス)
  - Healthcheck Proxy (VPC内のサービス監視、OIDC認証付き)
- **Cloud Run Jobs**: 
  - Saint Graph (配信ジョブ - 最大 1 時間)
  - News Collector (ニュース収集バッチ - 毎朝自動実行)
- **Compute Engine (GCE) + GPU**: Body Node (OBS + VoiceVox + Streamer)
- **Cloud Storage**: ニュース原稿とボイスファイルの共有ストレージ
- **Cloud Scheduler**: ワークフローの定期実行
- **Secret Manager**: API キーと YouTube 認証情報の安全な管理

## 前提条件

1. GCP プロジェクトが作成済み
2. 以下の API が有効化されている:
   - Compute Engine API
   - Cloud Run API
   - Cloud Scheduler API
   - Secret Manager API
   - Cloud Storage API
   - Artifact Registry API
   - Workflows API
   - Workflow Executions API
   - Serverless VPC Access API
3. `gcloud` CLI がインストール・認証済み
4. OpenTofu がインストール済み (>= 1.0)
5. Docker がインストール済み

## デプロイ手順

### 1. 準備 (Artifact Registry & Secret Manager)

まず、Docker イメージを保存するリポジトリと、必要なシークレットを作成します。

```bash
# プロジェクトIDを設定
export PROJECT_ID="your-gcp-project-id"
export REGION="asia-northeast1"
gcloud config set project $PROJECT_ID

# 必要なAPIの有効化
gcloud services enable \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  compute.googleapis.com \
  run.googleapis.com \
  cloudscheduler.googleapis.com

# Artifact Registry の作成
gcloud artifacts repositories create ai-tuber \
    --repository-format=docker \
    --location=${REGION}

# Docker認証設定
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# Google API Key をSecret Managerに保存 (必須)
echo -n "YOUR_GOOGLE_API_KEY" | gcloud secrets create google-api-key --data-file=-

# YouTube 配信用の認証情報を保存 (YouTube配信を行う場合)
echo -n '{"installed":{...}}' | gcloud secrets create youtube-client-secret --data-file=-
echo -n '{"token":"...","refresh_token":"..."}' | gcloud secrets create youtube-token --data-file=-
```

**注意**: YouTube 認証情報は、ローカルで OAuth フローを完了した後の JSON ファイルの内容をそのまま登録してください。

### 2. Docker イメージのビルドとプッシュ

**重要**: GCE の Body Node が正常に起動するには、**以下のすべてのイメージが Artifact Registry にプッシュされている必要があります**。いずれか一つでも欠けていると、スタートアップスクリプトが失敗します。

**Bash (Linux/macOS):**
```bash
export REGION="asia-northeast1"
export PROJECT_ID="your-gcp-project-id"
export REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/ai-tuber"

# Cloud Run 用イメージ
docker build -t ${REGISTRY}/saint-graph:latest -f src/saint_graph/Dockerfile .
docker push ${REGISTRY}/saint-graph:latest

docker build -t ${REGISTRY}/tools-weather:latest -f src/tools/weather/Dockerfile .
docker push ${REGISTRY}/tools-weather:latest

docker build -t ${REGISTRY}/news-collector:latest -f scripts/news_collector/Dockerfile .
docker push ${REGISTRY}/news-collector:latest

# GCE Body Node 用イメージ（必須！）
docker build -t ${REGISTRY}/body-streamer:latest -f src/body/streamer/Dockerfile .
docker push ${REGISTRY}/body-streamer:latest

docker build -t ${REGISTRY}/obs-studio:latest -f src/body/streamer/obs/Dockerfile .
docker push ${REGISTRY}/obs-studio:latest

docker build -t ${REGISTRY}/healthcheck-proxy:latest -f src/tools/health-proxy/Dockerfile src/tools/health-proxy
docker push ${REGISTRY}/healthcheck-proxy:latest
```

**PowerShell (Windows):**
```powershell
$REGION = "asia-northeast1"
$PROJECT_ID = "your-gcp-project-id"
$REGISTRY = "${REGION}-docker.pkg.dev/${PROJECT_ID}/ai-tuber"

# Cloud Run 用イメージ
docker build -t ${REGISTRY}/saint-graph:latest -f src/saint_graph/Dockerfile .
docker push ${REGISTRY}/saint-graph:latest

docker build -t ${REGISTRY}/tools-weather:latest -f src/tools/weather/Dockerfile .
docker push ${REGISTRY}/tools-weather:latest

docker build -t ${REGISTRY}/news-collector:latest -f scripts/news_collector/Dockerfile .
docker push ${REGISTRY}/news-collector:latest

docker build -t ${REGISTRY}/healthcheck-proxy:latest -f src/tools/health-proxy/Dockerfile src/tools/health-proxy
docker push ${REGISTRY}/healthcheck-proxy:latest

# GCE Body Node 用イメージ
docker build -t ${REGISTRY}/body-streamer:latest -f src/body/streamer/Dockerfile .
docker push ${REGISTRY}/body-streamer:latest

docker build -t ${REGISTRY}/obs-studio:latest -f src/body/streamer/obs/Dockerfile .
docker push ${REGISTRY}/obs-studio:latest
```

**イメージのプッシュを確認:**
```bash
# すべてのイメージがプッシュされたことを確認
gcloud artifacts docker images list ${REGION}-docker.pkg.dev/${PROJECT_ID}/ai-tuber

# 以下の6つのイメージが表示されることを確認してください：
# - saint-graph
# - tools-weather
# - news-collector
# - body-streamer
# - obs-studio
# - healthcheck-proxy
```

### 3. OpenTofu によるインフラのデプロイ

**イメージのプッシュ後**に OpenTofu でインフラをデプロイします：

```bash
cd opentofu

# 設定ファイルの作成
cp terraform.tfvars.example terraform.tfvars
# エディタで terraform.tfvars を編集し、project_id や admin_ip_ranges を設定

# デプロイ実行
tofu init
tofu apply
```

## 運用とモニタリング

### 自動実行スケジュール
Cloud Scheduler により、以下のスケジュールで毎日自動実行されます（Asia/Tokyo タイムゾーン）:

- **08:00**: **Cloud Workflows パイプライン開始**
  1. **News Collector**: ニュース収集と保存。
  2. **Start GCE**: Body Node を起動。
  3. **Wait Ready**: Healthcheck Proxy を経由し、Voicevox(50021) と OBS(8080) が応答するまで最大20分間リトライ待機。
  4. **Start Streaming**: Saint Graph ジョブを実行し配信開始。
  5. **Stop GCE**: 終了後に Body Node を自動停止。

### 手動での配信開始
スケジュールを待たずに手動で配信を開始したい場合：

```bash
# Cloud Run Job を手動実行
gcloud run jobs execute ai-tuber-saint-graph --region=asia-northeast1

# ※事前に Body Node (GCE) が起動していることを確認してください
gcloud compute instances start ai-tuber-body-node --zone=asia-northeast1-a
```

### GCE への SSH アクセス
Body Node にアクセスする必要がある場合（トラブルシューティングなど）:

```bash
# IAP 経由で安全に接続
gcloud compute ssh ai-tuber-body-node --zone=asia-northeast1-a --tunnel-through-iap

# コンテナの状態確認
docker ps
docker logs body-streamer
docker logs obs-studio
```

### noVNC でのブラウザアクセス
OBS の画面を Web ブラウザから確認できます:
- URL: `http://<GCE外部IP>:8080`
- `terraform.tfvars` で設定した `admin_ip_ranges` からのみアクセス可能

### 信頼性かコストか (Spot インスタンス)
デフォルトではコスト削減のため **Spot インスタンス** を使用しています。絶対に配信を中断させたくない場合は、`terraform.tfvars` で `enable_spot_instance = false` に設定してください。

### ログの確認
Ops Agent により、Docker コンテナのログも Cloud Logging に集約されます。

```bash
# Cloud Run Jobs のログ確認
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=ai-tuber-saint-graph" --limit 50

# GCE のシリアルポート出力（起動トラブル時）
gcloud compute instances get-serial-port-output ai-tuber-body-node --zone=asia-northeast1-a
```

### セキュリティアーキテクチャ (VPC & 認証)
GCE (Body Node) のステータスを安全に監視するために、以下の多層防御を採用しています：

- **VPC 隔離**: GCE のヘルスチェックポート (8000, 50021) はインターネット側には公開されていません。同一 VPC サブネットからの通信のみをファイアウォールで許可しています。
- **Healthcheck Proxy**: Cloud Workflows から直接 GCE の内部 IP にはアクセスできないため、専用のプロキシを Cloud Run 上に配置しています。
- **OIDC 認証**: プロキシ呼び出しには Google ID トークン (OIDC) が必要です。`ai-tuber-sa` サービスアカウントを持つ Workflows からの実行のみが承認されます。
- **Direct VPC Egress**: プロキシからの通信は VPC コネクタを経由して内部ネットワークのみを通ります。

### Git 不要の GCE 起動
以前は GCE 上で Git リポジトリをクローンしていましたが、現在は **Artifact Registry から直接イメージをプル** する方式に変更されています。これにより：
- SSH キーや GitHub トークンの設定が不要
- デプロイが高速かつシンプル
- セキュリティリスクが低減

### Saint Graph を Job として実装
Saint Graph（配信ロジック）は Cloud Run **Job** として実装されています。Service ではなく Job を選択した理由：
- HTTP サーバーの実装が不要（コードがシンプル）
- タイムアウトが最大 24 時間（Service は 60 分まで）
- バッチ処理（配信）としての実態に即している

### Secret Manager の活用
API キーや YouTube 認証情報は Secret Manager で一元管理され、環境変数として各サービスに注入されます。ソースコードや設定ファイルに機密情報を含める必要がありません。

## コスト見積もり

毎日1時間の配信を行う場合の月額コスト（参考値）：

| リソース | 使用量 | 月額費用 (USD) |
|---------|--------|---------------|
| **Compute Engine (L4 GPU, Spot)** | 1時間/日 × 30日 | $30-50 |
| **Cloud Run (Saint Graph, Weather)** | 軽微な使用 | $5-10 |
| **Cloud Run Jobs (News Collector)** | 1回/日 | $1-3 |
| **Cloud Storage** | 数MB | $1以下 |
| **ネットワーク (egress)** | YouTube 配信 | $5-10 |
| **合計** | - | **$40-70/月** |

**コスト最適化のポイント**:
- ✅ **Spot インスタンス**: 通常料金の 60-90% 割引（本構成のデフォルト）
- ✅ **使用時間の最小化**: 配信時のみ GCE を起動（Cloud Scheduler で自動化）
- ✅ **Scale to Zero**: Cloud Run は未使用時に課金なし

**注意**: 
- 通常の（非 Spot）インスタンスを使用した場合、月額 $200-300 程度になります
- 配信時間を増やすと、GCE の費用が比例して増加します
- リージョンによって料金が異なる場合があります

詳細な料金は [GCP Pricing Calculator](https://cloud.google.com/products/calculator) で試算できます。

## トラブルシューティング

### GCE Body Node でコンテナが起動しない

#### ステップ 0: スタートアップスクリプトの完了を待つ

**重要**: GCE インスタンス作成後、スタートアップスクリプトの完了には **5〜10分** かかります。特に NVIDIA GPU ドライバーのインストール時間が長いため、焦らずに待ってください。

```bash
# SSH 接続後、スタートアップスクリプトの状態を確認
sudo systemctl status google-startup-scripts.service

# リアルタイムでログを確認（進行状況を見る）
sudo journalctl -u google-startup-scripts.service -f
```

**スタートアップスクリプトの処理フロー**（合計 5〜10分）：
1. Ops Agent のインストールと設定（30秒）
2. Docker & Docker Compose のインストール（1〜2分）
3. Artifact Registry 認証設定（数秒）
4. **NVIDIA GPU ドライバーのインストール（3〜5分）** ← GCP 公式インストーラーを使用
5. **NVIDIA Container Toolkit のインストール（1分）**
6. 設定ファイル生成（.env, docker-compose.yml）（数秒）
7. Docker イメージのプル（1〜2分）
8. コンテナの起動（30秒）

**完了の確認方法**：
- ステータスが `Active: inactive (dead)` になる
- ログの最後に `=== AI Tuber Body Node started successfully ===` が表示される
- `sudo docker ps` でコンテナが起動していることを確認

**Docker がインストールされていない場合**：
```bash
sudo docker ps
# sudo: docker: command not found
```
→ まだスタートアップスクリプトが実行中です。上記のコマンドで進行状況を確認してください。

#### ステップ 1: エラーログの確認

スタートアップスクリプトが完了してもコンテナが起動しない場合、ログを確認してください：

```bash
# スタートアップスクリプトのログを確認
sudo journalctl -u google-startup-scripts.service -n 100 --no-pager

# または syslog から確認
sudo cat /var/log/syslog | grep startup-script | tail -50
```

#### よくあるエラーと対処法

##### 1. Permission denied (Artifact Registry)
```
Error: Permission 'artifactregistry.repositories.downloadArtifacts' denied
```

**原因**: サービスアカウントに Artifact Registry の読み取り権限がない  
**解決**: `iam.tf` に `roles/artifactregistry.reader` が追加されていることを確認し、`tofu apply` を実行

##### 2. Image not found
```
Error: asia-northeast1-docker.pkg.dev/${PROJECT_ID}/ai-tuber/obs-studio:latest: not found
```

**原因**: 必要なイメージが Artifact Registry にプッシュされていない  
**解決**: 以下のコマンドで確認し、不足しているイメージをビルド & プッシュ

```bash
# イメージ一覧を確認
gcloud artifacts docker images list asia-northeast1-docker.pkg.dev/${PROJECT_ID}/ai-tuber

# 必要なイメージ（5つ）:
# - saint-graph
# - tools-weather  
# - news-collector
# - body-streamer
# - obs-studio
```

不足しているイメージがあれば、ローカルで再度ビルド & プッシュしてください（手順 2 を参照）。

##### 3. NVIDIA driver/library error

**3-1. ライブラリが見つからない**
```
Error: nvidia-container-cli: initialization error: load library failed: libnvidia-ml.so
```

**原因**: NVIDIA GPU ドライバーがインストールされていない。またはランタイムが正しく設定されていない。
**解決**: スタートアップスクリプトは自動的に `nvidia-container-toolkit` を使用するように修正されました。手動で直す場合は以下を実行してください：

```bash
# GCE インスタンス上で実行
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

##### 4. 404 Not Found (Metadata error)
```
mkdir: cannot create directory '/opt/ai-tuber/data/mind/<!DOCTYPE html> ...' : File name too long
```
**原因**: インスタンスメタデータ（`character_name` など）の取得に失敗し、GCP が返した 404 エラーの HTML ページが変数に代入されてしまった。
**解決**: スクリプトは robust な取得（`get_metadata` 関数）を行うように更新されました。`compute.tf` に `character_name` メタデータが定義されているか確認してください。

##### 5. VoiceVox が Exit 1 で落ちる (権限エラー)
```
startup-script: dependency failed to start: container ai-tuber-voicevox-1 exited (1)
```
**原因**: マウントした `/opt/ai-tuber/data` の所有権が `root` になっており、VoiceVox コンテナ内ユーザーが書き込み/読み込みできずに落ちている。
**解決**: スタートアップスクリプターに `chmod -R 777 /opt/ai-tuber/data` を追加しました。手動で直す場合はインスタンス上で実行してください。

##### 4. コンテナが起動しているか確認

```bash
# GCE インスタンス上で実行
sudo docker ps

# ログを確認
sudo docker logs body-streamer
sudo docker logs obs-studio
sudo docker logs voicevox
```

#### 4. 手動でコンテナを起動

スタートアップスクリプトが失敗した場合、手動で起動できます：

```bash
cd /opt/ai-tuber
sudo docker-compose pull
sudo docker-compose up -d
```

## クリーンアップ
```bash
cd opentofu
tofu destroy
```

**注意**: シークレットや Artifact Registry のイメージは `tofu destroy` では削除されません。完全にクリーンアップする場合は手動で削除してください。

```bash
# シークレットの削除
gcloud secrets delete google-api-key
gcloud secrets delete youtube-client-secret
gcloud secrets delete youtube-token

# Artifact Registry のリポジトリ削除
gcloud artifacts repositories delete ai-tuber --location=asia-northeast1
```
