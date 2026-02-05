# GCP Deployment Guide (OpenTofu)

このディレクトリには、AI Tuber システムを Google Cloud Platform (GCP) にデプロイするための OpenTofu 設定と手順が含まれています。

## アーキテクチャ概要

- **Cloud Run**: Saint Graph, Tools Weather (ステートレスなロジック層)
- **Cloud Run Jobs**: News Collector (毎朝のバッチ処理)
- **Compute Engine (GCE) + GPU**: Body (OBS + VoiceVox + Streamer)
- **Cloud Storage**: ニュース原稿の共有ストレージ
- **Cloud Scheduler**: 毎朝の自動実行フロー

## 前提条件

1. GCP プロジェクトが作成済み
2. 以下の API が有効化されている:
   - Compute Engine API
   - Cloud Run API
   - Cloud Scheduler API
   - Secret Manager API
   - Cloud Storage API
3. `gcloud` CLI がインストール・認証済み
4. OpenTofu がインストール済み (>= 1.0)

## デプロイ手順

### 1. 準備 (Artifact Registry & Secret Manager)

まず、Docker イメージを保存するリポジトリと、必要なシークレットを作成します。

```bash
# プロジェクトIDを設定
export PROJECT_ID="your-gcp-project-id"
gcloud config set project $PROJECT_ID

# Artifact Registry の作成
gcloud services enable artifactregistry.googleapis.com
gcloud artifacts repositories create ai-tuber \
    --repository-format=docker \
    --location=asia-northeast1

# Docker認証設定
gcloud auth configure-docker asia-northeast1-docker.pkg.dev

# Google API Key をSecret Managerに保存 (必須)
echo -n "YOUR_GOOGLE_API_KEY" | gcloud secrets create google-api-key --data-file=-
```

### 2. Docker イメージのビルドとプッシュ

```bash
export REGION="asia-northeast1"
export REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/ai-tuber"

# 各サービスのビルドとプッシュ
docker build -t ${REGISTRY}/saint-graph:latest -f src/saint_graph/Dockerfile .
docker push ${REGISTRY}/saint-graph:latest

docker build -t ${REGISTRY}/tools-weather:latest -f src/tools/weather/Dockerfile .
docker push ${REGISTRY}/tools-weather:latest

docker build -t ${REGISTRY}/news-collector:latest -f scripts/news_collector/Dockerfile .
docker push ${REGISTRY}/news-collector:latest

docker build -t ${REGISTRY}/body-streamer:latest -f src/body/streamer/Dockerfile .
docker push ${REGISTRY}/body-streamer:latest
```

### 3. OpenTofu によるインフラのデプロイ

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
Cloud Scheduler により、以下のスケジュールで自動実行されます:
- **07:00**: News Collector ジョブ実行
- **07:15**: Body Node (GCE) 起動 (配信開始)
- **08:35**: Body Node (GCE) 停止 (配信終了)

### 信頼性かコストか (Spot インスタンス)
デフォルトではコスト削減のため **Spot インスタンス** を使用しています。絶対に配信を中断させたくない場合は、`terraform.tfvars` で `enable_spot_instance = false` に設定してください。

### ログの確認
Ops Agent により、Docker コンテナのログも Cloud Logging に集約されます。
```bash
# GCE のシリアルポート出力（起動トラブル時）
gcloud compute instances get-serial-port-output ai-tuber-body-node --zone=asia-northeast1-a
```

## クリーンアップ
```bash
cd opentofu
tofu destroy
```
