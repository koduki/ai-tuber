# The tiny IDP - Ops Portal

GCP リソースの運用・モニタリング用の、SvelteKit ベースのフレームワーク型 IDP です。

### 1. 運用ドキュメントの最新化とブランディング適用
[dashboard.md](file:///app/docs/components/dashboard.md) および [docs/README.md](file:///app/docs/README.md) を更新しました：
- **新名称の採用**: 「The tiny IDP - Ops Portal」という名称を統一的に採用。
- **フレームワーク型 IDP への再定義**: 単なるダッシュボードではなく、SvelteKit ベースのフレームワークであることを明記。
- **AI-Extensible の再定義**: 動的ロードの Extentions 方式ではなく、AI エージェントが直接ソースコードを生成・追加して拡張する設計（Coding-based extension）であることを強調。

### 2. ダッシュボード README の刷新
[README.md](file:///app/dashboard/README.md) において、ユーザーによる修正（The tiny IDP への改称、AI-Extensible の定義明確化）を尊重し、プロジェクトの性格をより正確に表現しました。
- **プロジェクト構造の解説**: `src/lib/modules` や `src/modules` 等の役割を明文化。
- **開発ガイド**: 環境変数の設定やローカル起動方法の追記。
- **モジュール追加手順**: AI エージェントによるコーディング拡張を前提とした 4 ステップの手順を記載。

## 検証結果

- [x] **整合性の確認**: `dashboard/README.md` での修正内容が、上位の `docs/` 配下のファイルにも一貫して反映されていることを確認しました。
- [x] **用語の統一**: 「フレームワーク型 IDP」「コーディングによる追加」といった表現に統一しました。
- **Compute**: GCE インスタンスの状態、IP アドレス、用途の表示。
- **Scheduler**: Cloud Scheduler ジョブの次回・前回実行結果と強制実行。
- **Workflows**: Cloud Workflows の定義情報と実行履歴。

## アーキテクチャ

SvelteKit をベースに、以下の構成で実装されています：

- **Frontend (Svelte 5)**: `src/routes/modules/[module_id]` で、`src/modules/[module_id]/View.svelte` を動的にロード。
- **Backend (Node.js)**: `src/modules/[module_id]/api.ts` 配下に各モジュールの API エンドポイントを定義。
- **GCP Client**: `@google-cloud/*` SDK をラップした `src/gcpClient.ts` が統一的なインターフェースを提供。

## セキュリティ・認証

本ダッシュボードは **OAuth2 Proxy** をサイドカーとして利用した認証方式を採用しています。

- **認証フロー**: Cloud Run の前面に配置された OAuth2 Proxy が Google ログインを処理し、認証済みのユーザー情報を HTTP ヘッダー（`x-forwarded-email` 等）としてダッシュボードに伝達します。
- **アクセス制御**: `src/hooks.server.ts` にて、伝達されたメールアドレスを `ALLOWED_EMAILS` 環境変数と照合し、認可を行います。
- **開発時の挙動**: ローカル環境ではモックユーザー（`dev@example.com`）として動作します。

## 運用上の注意
- API 呼び出しは、Cloud Run に付与されたサービスアカウントの権限で実行されます。
- `src/config.ts` で管理対象の GCP リソース名を一元管理しています。新しいリソースを追加する場合は、この設定ファイルを更新してください。
- クォータ制限に配慮し、フロントエンドでの自動更新は慎重に実装されています（デフォルト 60 秒）。
