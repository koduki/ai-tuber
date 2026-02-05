# GCP Deployment Guide

本ドキュメントでは、AI Tuber システムを Google Cloud Platform (GCP) にデプロイする手順を説明します。

## アーキテクチャ概要

- **Cloud Run**: Saint Graph, Tools Weather (ステートレスなロジック層)
- **Cloud Run Jobs**: News Collector (毎朝のバッチ処理)
- **Compute Engine (GCE) + GPU**: Body (OBS + VoiceVox + Streamer)
- **Cloud Storage**: ニュース原稿の共有ストレージ
- **Cloud Scheduler**: 毎朝の自動実行フロー

詳細は [実装計画](../implementation_plan.md) を参照してください。

## 前提条件

1. GCP プロジェクトが作成済み
2. 以下の API が有効化されている:
   - Compute Engine API
   - Cloud Run API
   - Cloud Scheduler API
   - Secret Manager API
   - Cloud Storage API
3. `gcloud` CLI がインストール・認証済み
4. Terraform がインストール済み (>= 1.0)

## デプロイ手順

### 1. サービスアカウントの作成

```bash
# プロジェクトIDを設定
export PROJECT_ID="your-gcp-project-id"
gcloud config set project $PROJECT_ID

# サービスアカウント作成
gcloud iam service-accounts create ai-tuber-sa \
    --display-name="AI Tuber Service Account"

# 必要な権限を付与
export SA_EMAIL="ai-tuber-sa@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/compute.instanceAdmin.v1"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/storage.objectUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/run.invoker"
```

### 2. Docker イメージのビルドとプッシュ

```bash
# Artifact Registry の有効化 (初回のみ)
gcloud services enable artifactregistry.googleapis.com
gcloud artifacts repositories create ai-tuber \
    --repository-format=docker \
    --location=asia-northeast1

# Docker認証設定
gcloud auth configure-docker asia-northeast1-docker.pkg.dev

# イメージのビルドとプッシュ
export REGION="asia-northeast1"
export REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/ai-tuber"

# Saint Graph
docker build -t ${REGISTRY}/saint-graph:latest -f src/saint_graph/Dockerfile .
docker push ${REGISTRY}/saint-graph:latest

# Tools Weather
docker build -t ${REGISTRY}/tools-weather:latest -f src/tools/weather/Dockerfile .
docker push ${REGISTRY}/tools-weather:latest

# News Collector
docker build -t ${REGISTRY}/news-collector:latest -f scripts/news_collector/Dockerfile .
docker push ${REGISTRY}/news-collector:latest

# Body Streamer (GCE用 - Docker Hubにプッシュするか、スタートアップスクリプトでビルド)
docker build -t ${REGISTRY}/body-streamer:latest -f src/body/streamer/Dockerfile .
docker push ${REGISTRY}/body-streamer:latest
```

### 3. Secrets の設定

```bash
# Google API Key をSecret Managerに保存
echo -n "YOUR_GOOGLE_API_KEY" | gcloud secrets create google-api-key --data-file=-

# YouTube認証情報 (配信する場合)
gcloud secrets create youtube-client-secret --data-file=/path/to/client_secret.json
gcloud secrets create youtube-token --data-file=/path/to/token.json
```

### 4. Terraform でインフラをデプロイ

```bash
cd terraform

# terraform.tfvars を作成
cp terraform.tfvars.example terraform.tfvars
# エディタで terraform.tfvars を編集し、適切な値を設定

# Terraformの初期化
terraform init

# デプロイ計画の確認
terraform plan

# デプロイ実行
terraform apply
```

### 5. 動作確認

```bash
# News Collector ジョブを手動実行
gcloud run jobs execute ai-tuber-news-collector --region=asia-northeast1

# GCS にファイルがアップロードされたか確認
gsutil ls gs://YOUR_BUCKET_NAME/news/

# Body Node を手動起動
gcloud compute instances start ai-tuber-body-node --zone=asia-northeast1-a

# ログ確認
gcloud compute ssh ai-tuber-body-node --zone=asia-northeast1-a
# インスタンス内で
cd /opt/ai-tuber
docker-compose logs -f
```

## 運用

### 自動実行スケジュール

Cloud Scheduler により、以下のスケジュールで自動実行されます:

- **07:00**: News Collector ジョブ実行
- **07:15**: Body Node (GCE) 起動
- **08:35**: Body Node (GCE) 停止

### コスト最適化

- **Spot Instance**: Body Node はデフォルトで Spot インスタンスを使用します (60-90% コスト削減)
- **スケール to Zero**: Cloud Run は使用していない時間は課金されません
- **自動停止**: 配信時間外は GCE インスタンスを停止

### 信頼性かコストか (Spot インスタンスの注意点)

Body Node に **Spot インスタンス** を使用する場合、以下のリスクがあります：
- 配信中に Google Cloud 側の都合でインスタンスが強制終了される可能性がある（30秒前に通知）。
- 再起動は自動では行われません。

**「絶対に配信を止めたくない」** 本番運用の場合は、`terraform/terraform.tfvars` で Spot を無効にすることを検討してください：
```hcl
enable_spot_instance = false
```
※ この場合、費用は Spot 利用時の約3-5倍になります。

### モニタリング

```bash
# Cloud Run のログ確認
gcloud logging read "resource.type=cloud_run_revision" --limit=50

# GCE のログ確認
gcloud compute instances get-serial-port-output ai-tuber-body-node --zone=asia-northeast1-a
```

## トラブルシューティング

### GCE インスタンスが起動しない

1. GPU クォータを確認:
   ```bash
   gcloud compute project-info describe --project=$PROJECT_ID
   ```
2. GPU が利用可能なゾーンを確認:
   ```bash
   gcloud compute accelerator-types list --filter="zone:asia-northeast1-a"
   ```

### Cloud Run から GCE に接続できない

1. VPC Connector が正しく設定されているか確認
2. Firewall ルールを確認

### News Collector が失敗する

1. Secret Manager の権限を確認
2. GCS バケットの権限を確認
3. Cloud Run Job のログを確認:
   ```bash
   gcloud logging read "resource.type=cloud_run_job" --limit=50
   ```

## クリーンアップ

```bash
# Terraformで全リソースを削除
cd terraform
terraform destroy

# 手動で作成したリソースの削除
gcloud secrets delete google-api-key
gcloud iam service-accounts delete $SA_EMAIL
```

## 次のステップ

- [アーキテクチャ概要](architecture/overview.md)
- [ローカル開発環境](README.md#開発環境のセットアップ)
- [トラブルシューティング](docs/knowledge/troubleshooting.md)
