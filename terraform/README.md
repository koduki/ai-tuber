# Terraform Configuration for AI Tuber

このディレクトリには、AI Tuber システムを GCP にデプロイするための Terraform 設定が含まれています。

## 構成ファイル

- `main.tf` - プロバイダーと変数の定義
- `storage.tf` - Cloud Storage バケットの設定
- `network.tf` - VPC とファイアウォールルール
- `compute.tf` - Compute Engine (Body Node) の設定
- `cloudrun.tf` - Cloud Run サービスとジョブ
- `secrets.tf` - Secret Manager の設定
- `scheduler.tf` - Cloud Scheduler ジョブ (自動実行)
- `terraform.tfvars.example` - 変数の例 (コピーして使用)

## 前提条件

1. Terraform >= 1.0 がインストール済み
2. gcloud CLI がインストール・認証済み
3. GCP プロジェクトが作成済み

## 使用方法

### 1. 変数ファイルの作成

```bash
cp terraform.tfvars.example terraform.tfvars
```

`terraform.tfvars` を編集し、適切な値を設定してください：

```hcl
project_id              = "your-gcp-project-id"
region                  = "asia-northeast1"
zone                    = "asia-northeast1-a"
bucket_name             = "ai-tuber-data-YOUR_PROJECT_ID"
service_account_email   = "ai-tuber-sa@your-gcp-project-id.iam.gserviceaccount.com"
```

### 2. 初期化

```bash
terraform init
```

### 3. デプロイ計画の確認

```bash
terraform plan
```

### 4. デプロイ

```bash
terraform apply
```

### 5. リソースの削除

```bash
terraform destroy
```

## 注意事項

- **GPU クォータ**: L4 GPU を使用するには、プロジェクトで GPU クォータの増加申請が必要な場合があります
- **Secret Manager**: API キーは手動で設定する必要があります（`secrets.tf` 参照）
- **Spot インスタンス**: コスト削減のため Body Node は Spot インスタンスです。中断される可能性がありますが、通常 1-2 時間の配信には十分です

## デプロイ後の設定

詳細は [GCP デプロイガイド](../docs/deployment/gcp.md) を参照してください。
