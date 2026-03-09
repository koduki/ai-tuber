# GCP Ops Portal Dashboard

AI Tuber プラットフォームの GCP リソースの状態を可視化するための運用ダッシュボードです。

## 概要

モックデザインをベースに、GCP API から実際のデータを取得して表示する運用ポータルです。
以下のリソースのステータス、メタデータ、実行履歴を一覧表示します。

- **Cloud Scheduler**: 毎日実行されるデータ更新ジョブの状態
- **Cloud Workflows**: ストリーミングパイプラインの実行履歴
- **Cloud Run (Services/Jobs)**: サーバー・バッチジョブの稼働状態
- **Compute Engine (GCE)**: Body ノードのインスタンス状態と IP 
- **Cloud Build**: 各コンポーネントのビルド履歴

## 技術スタック

- **Backend**: TypeScript / Express (API Server)
- **Frontend**: Vanilla HTML / CSS / JavaScript (No framework)
- **Infra**: OpenTofu (GCP Provisioning), Cloud Run (Hosting)
- **CI/CD**: Cloud Build (Auto deployment)

## ディレクトリ構成

```text
src/dashboard/
├── Dockerfile          # マルチステージビルド定義
├── package.json        # 依存関係定義
├── src/                # バックエンド TypeScript 
│   ├── config.ts       # 環境設定
│   ├── gcpClient.ts    # GCP SDK 連携ロジック
│   └── server.ts       # Express サーバー
├── public/             # フロントエンド静的ファイル
│   ├── index.html      # メイン UI
│   ├── style.css       # GCP Console 風デザインの CSS 
│   └── app.js          # API フェッチ & 動的レンダリング
└── tsconfig.json       # TypeScript 設定
```

## ローカル開発

### 1. 依存関係のインストール
Node.js 20+ が必要です。

```bash
cd src/dashboard
npm install
```

### 2. 環境変数の設定
ローカルで動かす場合は、GCP 認証 (`gcloud auth application-default login`) が必要です。

```bash
export GCP_PROJECT_ID=your-project-id
export GCP_REGION=asia-northeast1
export GCP_ZONE=asia-northeast1-a
```

### 3. テスト起動 (Docker 推奨)

ローカル環境の `gcloud` 認証情報を利用して、コンテナ内でダッシュボードを起動します。

```bash
# 1. 認証情報のコピー (一度だけ実行)
cp ~/.config/gcloud/application_default_credentials.json gcp-creds.json

# 2. 起動
docker compose -f docker-compose.local.yml up --build
```

起動後、 `http://localhost:3000` にアクセスしてください。

### (参考) Node.js 直接起動

```bash
npm run dev
```

## デプロイ

変更を `main` (または `dev/.*`) ブランチにプッシュすると、Cloud Build が自動的にイメージをビルドし、Cloud Run (`ai-tuber-dashboard`) へデプロイします。

手動デプロイする場合:
```bash
gcloud builds submit --config cloudbuild-dashboard.yaml --substitutions=_REGION=asia-northeast1,_REPOSITORY=ai-tuber .
```

## セキュリティとアクセス制限

開発効率と安全性を考慮し、以下のアクセス制限を行っています。

1.  **IAM によるアクセス制御**: 
    - 特定の `allUsers` などの公開アクセス権限は付与されていません。
    - Cloud Run の起動権限を持つ IAM ユーザーのみが閲覧可能です。

2.  **ブラウザからの閲覧方法**: 
    セキュリティ制限により直接 URL を開くと 403 エラーになります。以下のプロキシコマンドを使用してアクセスしてください。

```bash
gcloud run services proxy ai-tuber-dashboard --region asia-northeast1
```

表示されたローカル URL（例: `http://127.0.0.1:8080`）をブラウザで開いてください。

---

## 注意事項
- **コスト情報**: Billing API へのアクセスには強力な権限が必要なため、現在はプレースホルダ表示となっています。
- **自動更新**: フロントエンドは 60 秒間隔でデータの再取得を自動的に行います。
