# GCP デプロイ実装サマリー

## 実装内容

以下の3つのタスクを完了しました：

### 1. GCS 連携の実装 ✅

**News Collector (アップロード側)**
- `scripts/news_collector/news_agent.py`: GCS アップロード機能を追加
- `scripts/news_collector/requirements.txt`: `google-cloud-storage` 依存関係を追加
- `scripts/news_collector/Dockerfile`: Cloud Run Job 用の Dockerfile を作成

**Saint Graph (ダウンロード側)**
- `src/saint_graph/news_service.py`: GCS からのダウンロード機能を追加（フォールバック付き）
- `src/saint_graph/requirements.txt`: `google-cloud-storage` 依存関係を追加

**環境変数**
- `.env.example`: `GCS_BUCKET_NAME` 環境変数を追加

**動作**:
1. News Collector がニュースを収集し、ローカルファイルと GCS の両方に保存
2. Saint Graph は GCS から優先的にダウンロード、失敗時はローカルにフォールバック

---

### 2. Infrastructure as Code (Terraform) ✅

`terraform/` ディレクトリに以下のファイルを作成：

**コア設定**
- `main.tf`: プロバイダーと変数定義
- `storage.tf`: Cloud Storage バケット
- `network.tf`: VPC、サブネット、ファイアウォールルール
- `secrets.tf`: Secret Manager の設定

**コンピュートリソース**
- `compute.tf`: Compute Engine (Body Node) - GPU + Spot インスタンス
- `cloudrun.tf`: Cloud Run サービス (Saint Graph, Tools Weather) と Cloud Run Job (News Collector)

**自動化**
- `scheduler.tf`: Cloud Scheduler ジョブ
  - 07:00: News Collector 実行
  - 07:15: Body Node 起動
  - 08:35: Body Node 停止

**ドキュメント**
- `terraform.tfvars.example`: 変数のサンプル
- `terraform/README.md`: Terraform 使用方法

---

### 3. Startup/Shutdown Scripts ✅

**GCE 用スクリプト**
- `scripts/gce/startup.sh`: 
  - Docker、Docker Compose、NVIDIA ランタイムのインストール
  - リポジトリのクローンまたは更新
  - Secret Manager から API キーを取得
  - `docker-compose.gce.yml` でサービス起動
  
- `scripts/gce/shutdown.sh`:
  - Docker Compose でサービスの安全な停止

**GCE 専用 Docker Compose**
- `docker-compose.gce.yml`: Body サービスのみ (Streamer, VoiceVox, OBS)

---

## ドキュメント更新 ✅

**新規作成**
- `docs/deployment/gcp.md`: 完全なデプロイガイド
  - 前提条件
  - ステップバイステップの手順
  - トラブルシューティング
  - 運用ガイド

**既存ドキュメントの更新**
- `README.md`: デプロイセクションを追加、GCP デプロイガイドへのリンク
- `docs/architecture/overview.md`: デプロイ環境セクションを追加
- `.gitignore`: Terraform 関連ファイルを除外

---

## アーキテクチャ概要

```
┌─────────────────────────────────────────────────────┐
│           Cloud Scheduler (毎朝自動実行)              │
│  07:00 News  →  07:15 GCE起動  →  08:35 GCE停止    │
└─────────────────────────────────────────────────────┘
                        ↓
    ┌───────────────────────────────────────────┐
    │        Serverless Layer (Cloud Run)       │
    │  ┌──────────────┐  ┌──────────────┐     │
    │  │ Saint Graph  │  │Tools Weather │     │
    │  └──────────────┘  └──────────────┘     │
    │  ┌──────────────┐                       │
    │  │ News Collector│ (Cloud Run Job)      │
    │  └──────────────┘                       │
    └───────────────────────────────────────────┘
                ↓                    ↓
    ┌─────────────────────┐  ┌──────────────┐
    │  Cloud Storage (GCS) │  │   Body Node  │
    │  - news_script.md    │  │  (Compute    │
    └─────────────────────┘  │   Engine)    │
                             │  ┌─────────┐ │
                             │  │Streamer │ │
                             │  │VoiceVox │ │
                             │  │  OBS    │ │
                             │  └─────────┘ │
                             └──────────────┘
                                    ↓
                            ┌──────────────┐
                            │ YouTube Live │
                            └──────────────┘
```

---

## 次のステップ

1. **GCP プロジェクトの準備**
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **サービスアカウントの作成**
   ```bash
   # docs/deployment/gcp.md の手順1を参照
   ```

3. **Docker イメージのビルド & プッシュ**
   ```bash
   # docs/deployment/gcp.md の手順2を参照
   ```

4. **Secrets の設定**
   ```bash
   echo -n "YOUR_API_KEY" | gcloud secrets create google-api-key --data-file=-
   ```

5. **Terraform でデプロイ**
   ```bash
   cd terraform
   cp terraform.tfvars.example terraform.tfvars
   # terraform.tfvars を編集
   terraform init
   terraform apply
   ```

6. **動作確認**
   ```bash
   # News Collector ジョブを手動実行
   gcloud run jobs execute ai-tuber-news-collector --region=asia-northeast1
   ```

詳細な手順は **[docs/deployment/gcp.md](docs/deployment/gcp.md)** を参照してください。

---

## コスト見積もり (月額)

| リソース | 使用量 | 月額費用 (参考) |
|---------|--------|----------------|
| Compute Engine (L4 GPU, Spot) | 1時間/日 × 30日 | $30-50 |
| Cloud Run (Saint Graph, Weather) | 軽微 | $5-10 |
| Cloud Run Jobs (News Collector) | 1回/日 | $1-3 |
| Cloud Storage | 数MB | $1以下 |
| **合計** | - | **$40-70/月** |

※ Spot インスタンスの割引 (60-90%) を適用した場合。通常インスタンスの場合は $200-300/月程度。

---

## トラブルシューティング

詳細は `docs/deployment/gcp.md` の「トラブルシューティング」セクションを参照してください。

よくある問題:
- GPU クォータ不足 → GCP コンソールでクォータ増加申請
- VPC 接続エラー → Serverless VPC Connector の設定確認
- Secret Manager 権限エラー → サービスアカウントの IAM ロール確認
