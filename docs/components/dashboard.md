# The tiny IDP - Ops Portal

GCP リソースの運用・モニタリング用の、SvelteKit ベースのフレームワーク型 IDP です。
AI エージェントが直接ソースコードを生成・追加して拡張することを前提とした「AI-Extensible」な設計を採用しています。

## 特徴

- **フレームワーク型 IDP**: 単なる固定的なダッシュボードではなく、モジュールを追加することで機能を拡張できるプラットフォームです。
- **AI-Extensible (Coding-based extension)**: 動的ロードの Extentions 方式ではなく、AI エージェントが直接ソースコード（View, API, Metadata）を追加して統合する設計です。
- **GCP Native**: Google Cloud SDK を使用して、Cloud Run, Compute, Scheduler, Workflows などのリソースを直接管理します。

## 設計思想 (Design Philosophy)

本プロジェクトは以下の原則に基づいて設計されています：

1.  **シンプルかつ明確であること (Simple & Explicit)**:
    高度な抽象化よりも、構造が単純で、何を行っているかが一目でわかる「明示性」を優先します。
2.  **冗長性の許容 (Embrace Redundancy)**:
    モジュール間の独立性を高めるため、あえて共通化を避け、各モジュールにボイラープレート（API 定義や UI コンポーネント）を持たせることを許容します。これにより、モジュール単体での理解と改修が容易になります。
3.  **AI による自律的な拡張 (AI-First Extensibility)**:
    AI エージェントが既存のモジュールを「コピー＆ペースト」して新しい機能を作成できることを前提としています。複雑なメタプログラミングや動的なプラグイン機構を避け、コードベースの静的な拡張を推奨します。

## 主要機能

- **Cloud Run**: サービスおよびジョブの状態表示、リージョン、URI、認証設定の確認。
- **Compute**: GCE インスタンスの状態、IP アドレス、用途の表示。
- **Scheduler**: Cloud Scheduler ジョブの次回・前回実行結果と強制実行。
- **Workflows**: Cloud Workflows の定義情報と実行履歴。
- **Billing**: プロジェクトの請求状況と予算の可視化。

## アーキテクチャ

SvelteKit をベースに、以下の構成で実装されています：

- **Frontend (Svelte 5)**: `src/routes/modules/[module_id]/+page.svelte` にて、`src/modules/[module_id]/View.svelte` を動的にインポートして表示します。
- **Backend (Node.js)**: `src/routes/api/modules/[module_id]/[slug]/+server.ts` が、`src/modules/[module_id]/api.ts` 内の各エンドポイントを呼び出す「パススルー」構成です。
- **GCP Client**: `@google-cloud/*` SDK をラップした `src/gcpClient.ts` が提供されますが、モジュールの独立性のために、`api.ts` 内で直接 SDK や Rest API を呼び出す実装も推奨されます。

## セキュリティ・認証

本ダッシュボードは **OAuth2 Proxy** をサイドカーとして利用した認証方式を採用しています。

- **認証フロー**: Cloud Run の前面に配置された OAuth2 Proxy が Google ログインを処理し、認証済みのユーザー情報を HTTP ヘッダー（`x-forwarded-email` 等）としてダッシュボードに伝達します。
- **アクセス制御**: `src/hooks.server.ts` にて、伝達されたメールアドレスを `ALLOWED_EMAILS` 環境変数と照合し、認可を行います。
- **開発時の挙動**: ローカル開発（`npm run dev`）では、OAuth2 Proxy が存在しないため、モックユーザー（`dev@example.com`）として動作します。

## 運用上の注意

- API 呼び出しは、Cloud Run に付与されたサービスアカウント（IDP 用のカスタムロール推奨）の権限で実行されます。
- `src/config.ts` で管理対象の GCP リソース名を一元管理しています。新しいリソースを追加する場合は、この設定ファイルを更新してください。
- クォータ制限に配慮し、フロントエンドでの自動更新は慎重に実装されています（デフォルト 60 秒）。
- ESM (ES Modules) 環境で動作するため、ライブラリの非互換性（特に SDK の Proto デコード問題）が発生した場合は、`src/gcpClient.ts` の `gcpFetch` を使用した REST API 呼び出しを検討してください。
