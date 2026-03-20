# The tiny IDP - Ops Portal 

GCP リソースの運用状況を可視化・管理するための、SvelteKit ベースのフレームワーク型 IDP です。

## 特徴
- **AI-Extensible**: 動的ロードのExtentionsではなく、AI エージェントが新しいモジュールをコーディングで追加する設計。
- **GCP Native**: SDK 経由で Cloud Run, Workflows, Scheduler 等を直接操作・監視。
- **OAuth2 Proxy Integration**: サイドカー方式による柔軟な認証。

## プロジェクト構造

```text
dashboard/
├── src/
│   ├── modules/          # 各機能のモジュール (Backend & Frontend)
│   │   └── [module_id]/
│   │       ├── View.svelte  # フロントエンド UI
│   │       ├── api.ts      # バックエンド API (SvelteKit Endpoint 形式)
│   │       └── index.ts    # メタデータ定義
│   ├── routes/           # SvelteKit ルーティング
│   ├── gcpClient.ts      # GCP SDK / REST API ラッパー
│   ├── hooks.server.ts   # 認証・認可ロジック
│   └── config.ts         # リソース名の設定管理
├── static/               # 静的アセット
└── svelte.config.js      # SvelteKit 設定 (adapter-node 使用)
```

## デザイン制約と実装原則

このダッシュボードを正常にビルド・運用するために、以下の制約を厳守してください：

1.  **シンプルかつ明確 (Simple & Explicit)**:
    - 過剰な共通化や複雑な抽象化は避けてください。
    - 各モジュールが自己完結し、他のモジュールを読まなくても理解できる状態（Explicit）を目指してください。
    - 新しいモジュールを作る際は、既存のモジュールのコードを「コピー＆ペースト」して改変する手法を推奨します。

## 開発ガイド

### 環境変数の設定

`.env` または Docker デプロイ時の環境変数として以下を設定します：

- `GCP_PROJECT_ID`: 対象の GCP プロジェクト ID
- `ALLOWED_EMAILS`: アクセスを許可する Google アカウントのメールアドレス（カンマ区切り）

### 開発サーバーの起動

```bash
npm install
npm run dev
```

ローカル開発時は、OAuth2 Proxy がないため `hooks.server.ts` が `dev@example.com` としてモック認証を行います。

### 新しいモジュールの追加手順

1.  **モジュールディレクトリの作成**: `src/modules/[module_name]` を作成します。既存の `cloud-run` などをコピーするのが最速です。
2.  **Metadata の定義**: `index.ts` を作成し、`metadata` を export します。
3.  **Backend API の実装**: `api.ts` を作成します。SvelteKit 互換の形式で、`GET` や `POST` オブジェクトをエクスポートしてください。冗長であっても、モジュール内で直接 API を叩く実装を検討してください。
4.  **Frontend View の実装**: `View.svelte` を作成し、UI を実装します。
5.  **ナビゲーションへの追加**: プログラムによって `src/routes/api/manifest` から自動取得されます。

## ビルドとデプロイ

### ローカルビルド確認

```bash
npm run build
# build/ ディレクトリに出力されます
```

### Cloud Build によるデプロイ

```bash
gcloud builds submit --config cloudbuild-dashboard.yaml .
```

本番環境（Cloud Run）では、認証に OAuth2 Proxy サイドカーを使用します。
**注意**: デプロイ時は `gcloud beta run services replace` ではなく `gcloud run services update` (または terraform) を使用してください。`replace` を使用すると設定済みのサイドカーが消失する恐れがあります。

## トラブルシューティング

詳細は [プロジェクト共通のトラブルシューティング](../../docs/knowledge/troubleshooting.md) を参照してください。

- **404 Not Found**: `/api/modules/...` が 404 になる場合、`src/routes/api/modules/[module_id]/[slug]/+server.ts` のパス解決（glob パターン）が `src/modules` を正しく指しているか確認してください。
- **ReferenceError: require is not defined**: ESM 環境で `require` を使用しています。`import` に書き換えてください。
- **WorkflowsClient is not a constructor**: `@google-cloud/workflows` SDK の ESM 互換性問題です。REST API 方式に切り替えてください。
