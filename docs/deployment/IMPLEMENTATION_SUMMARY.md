# GCP デプロイ実装サマリー

このドキュメントは、GCP デプロイ機能の実装変更履歴を記録しています。詳細な仕様やアーキテクチャについては、各コンポーネントのドキュメントを参照してください。

---

## 実装変更履歴

### 2026-02-05: NVIDIA GPU ドライバーインストール方法の改善

**変更内容**:
- GCE スタートアップスクリプトのNVIDIA ドライバーインストール方法を変更
- CUDA リポジトリからの直接インストール → **GCP 公式GPU ドライバーインストーラーに変更**

**理由**:
- GCP の Ubuntu カーネル (6.8.0-*-gcp) と CUDA ドライバー 550 の DKMS ビルドの互換性問題を解決
- GCP 公式インストーラーはカーネル互換性を自動的に処理

**変更ファイル**:
- `scripts/gce/startup.sh`

**詳細**: [opentofu/README.md - トラブルシューティング](../../opentofu/README.md#トラブルシューティング)

---

### 2026-02-05: ドキュメント整理とコード整合性確認

**変更内容**:
- スタートアップスクリプトの重複した Artifact Registry 認証設定を削除
- README の処理フロー記述を実際のスクリプトに合わせて更新（8ステップ）
- Secret 作成コマンドを `gcloud secrets create` に修正（以前は `versions add`）

**変更ファイル**:
- `scripts/gce/startup.sh`
- `opentofu/README.md`
- `README.md`（誤字修正）

---

### 2026-02-04: GCS 連携の実装 ✅

**変更内容**:
News Collector と Saint Graph に Cloud Storage 連携機能を追加しました。

**主な変更**:
- News Collector: GCS へのアップロード機能を追加
- Saint Graph: GCS からのダウンロード機能を追加（ローカルファイルへのフォールバック付き）
- 環境変数 `GCS_BUCKET_NAME` の追加

**変更ファイル**:
- `scripts/news_collector/news_agent.py`
- `scripts/news_collector/requirements.txt`
- `scripts/news_collector/Dockerfile`
- `src/saint_graph/news_service.py`
- `src/saint_graph/requirements.txt`
- `.env.example`

**詳細ドキュメント**:
- [News Collector - GCS連携](../components/saint-graph/news-collector.md#gcs-連携とクラウドデプロイ)
- [News Service - Cloud Storage連携](../components/saint-graph/news-service.md#cloud-storage-連携)

---

### 2026-02-04: Infrastructure as Code (OpenTofu) ✅

**変更内容**:
GCP リソースを OpenTofu で管理できるように IaC を実装しました。

**作成ファイル**:
`opentofu/` ディレクトリに以下のファイルを作成：
- `main.tf`, `storage.tf`, `network.tf`, `secrets.tf`, `iam.tf`
- `compute.tf`, `cloudrun.tf`, `scheduler.tf`
- `terraform.tfvars.example`, `README.md`

**詳細**: [GCP デプロイガイド](../../opentofu/README.md)

---

### 2026-02-04: Secret Manager 統合 ✅

**変更内容**:
API キーや YouTube 認証情報を Secret Manager で管理できるようにしました。

**主な変更**:
- YouTube 用シークレット定義を追加（`youtube-client-secret`, `youtube-token`）
- Cloud Run への環境変数注入設定

**変更ファイル**:
- `opentofu/secrets.tf`
- `opentofu/cloudrun.tf`

**詳細**: [opentofu/README.md - Secret Manager設定](../../opentofu/README.md#1-準備-artifact-registry--secret-manager)

---

### 2026-02-04: GCE Startup Script の最適化 ✅

**変更内容**:
Git リポジトリのクローンを廃止し、Artifact Registry から直接イメージをプルする方式に変更しました。

**メリット**:
- SSH キーやトークンの設定が不要
- デプロイが高速かつシンプル
- セキュリティリスクが低減

**変更ファイル**:
- `scripts/gce/startup.sh`

**詳細**: [アーキテクチャ概要 - GCP本番環境](../architecture/overview.md#gcp-本番環境-ハイブリッド構成)

---

### 2026-02-04: Saint Graph の Cloud Run Job 化 ✅

**変更内容**:
Saint Graph を Cloud Run Service から **Cloud Run Job** に変更しました。

**理由**:
- HTTP サーバーの実装が不要（コードがシンプル）
- 長時間配信に対応（最大 24 時間まで可能）
- バッチ処理（配信）としての実態に即している
- ヘルスチェック不要で堅牢

**変更ファイル**:
- `opentofu/cloudrun.tf`
- `src/saint_graph/main.py`

**詳細**: [アーキテクチャ概要 - Saint Graph を Job として実装した理由](../architecture/overview.md#gcp-本番環境-ハイブリッド構成)

## ドキュメント更新 ✅

**新規作成**
- `opentofu/README.md`: 完全なデプロイガイド
  - Artifact Registry、Secret Manager、OpenTofu 手順を統合
  - YouTube 認証情報の設定方法を追加
  - 手動での配信開始方法を記載
  - PowerShell 対応のコマンド例も追加

**既存ドキュメントの更新**
- `README.md`: デプロイセクションを追加、GCP デプロイガイドへのリンク
- `docs/architecture/overview.md`: デプロイ環境セクションを追加
- `.gitignore`: OpenTofu 関連ファイルを除外

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

2. **準備 (Artifact Registry & Secrets)**
   ```bash
   # opentofu/README.md の手順1および3を参照
   ```

3. **Docker イメージのビルド & プッシュ**
   ```bash
   # opentofu/README.md の手順2を参照
   ```

5. **OpenTofu でデプロイ**
   ```bash
   cd opentofu
   cp terraform.tfvars.example terraform.tfvars
   # terraform.tfvars を編集
   tofu init
   tofu apply
   ```

6. **動作確認**
   ```bash
   # News Collector ジョブを手動実行
   gcloud run jobs execute ai-tuber-news-collector --region=asia-northeast1
   ```

詳細な手順は **[opentofu/README.md](../../opentofu/README.md)** を参照してください。

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

詳細は `opentofu/README.md` を参照してください。

よくある問題:
- GPU クォータ不足 → GCP コンソールでクォータ増加申請
- VPC 接続エラー → Serverless VPC Connector の設定確認
- Secret Manager 権限エラー → サービスアカウントの IAM ロール確認
