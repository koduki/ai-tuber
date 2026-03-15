# Dashboard (Ops Portal)

GCP リソースの運用・モニタリング用のダッシュボードコンポーネントです。

## 基本機能

- [x] リソース状態の一覧表示 (Scheduler, Workflows, Run, GCE, Build)
- [x] メタデータと外部 IP の表示
- [x] 実行履歴の取得
- [x] 自動リフレッシュ機能

## 詳細ドキュメント

開発・セットアップ・デプロイに関する詳細は、コンポーネント配下の README を参照してください。

- [dashboard/README.md](file:///app/dashboard/README.md)

## セキュリティに関する特記事項

Identity-aware Proxy (IAP) を未設定の状態では、Cloud Run の IAM 認証を利用しています。
閲覧の際は `gcloud run services proxy` コマンドを使用して、認証情報を付与したプロキシ経由でアクセスすることを標準としています。

---

## 運用上の注意
- API 呼び出しはバックエンドサービスアカウントの権限で実行されます。
- クォータ制限に配慮し、デフォルトの自動更新間隔は 60 秒に設定されています。
