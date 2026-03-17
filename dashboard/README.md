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
│   │       ├── api.ts      # バックエンド API (Express Router)
│   │       └── index.ts    # メタデータ定義
│   ├── routes/           # SvelteKit ルーティング
│   ├── gcpClient.ts      # GCP SDK ラッパー
│   ├── hooks.server.ts   # 認証・認和ロジック
│   └── config.ts         # リソース名の設定管理
├── static/               # 静的アセット
└── svelte.config.js      # SvelteKit 設定 (adapter-node 使用)
```

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

1.  **モジュールディレクトリの作成**: `src/modules/[module_name]` を作成します。
2.  **Metadata の定義**: `index.ts` を作成し、`metadata` を export します。
3.  **Backend API の実装**: `api.ts` を作成し、Router を指定します。
4.  **Frontend View の実装**: `View.svelte` を作成し、UI を実装します。
5.  **ナビゲーションへの追加**: `src/lib/components/Sidebar.svelte` 等にリンクを追加します。

## ビルドとデプロイ

```bash
npm run build
# build/ ディレクトリに出力されます
node build
```

本番環境（Cloud Run）では、`Dockerfile` を使用してビルド・実行されます。
認証は前面の OAuth2 Proxy サイドカーが担当するため、アプリケーション単体で公開しないでください。
