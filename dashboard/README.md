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
│   ├── modules/          # バックエンド API モジュール (Express-like Router)
│   ├── lib/
│   │   └── modules/      # フロントエンド UI モジュール (Svelte components)
│   ├── routes/           # SvelteKit ルーティング
│   │   └── modules/      # モジュールの動的ロード用エンドポイント
│   ├── gcpClient.ts      # GCP SDK ラッパー
│   ├── hooks.server.ts   # 認証・認可ロジック (OAuth2 Proxy ヘッダー処理)
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

1.  **Backend API の作成**: `src/modules/[module_name]/api.ts` を作成し、Router を定義します。
2.  **Frontend View の作成**: `src/lib/modules/[module_name]/View.svelte` を作成し、UI を実装します。
3.  **API の登録**: `src/server.ts` (または対応する API 集約箇所) に作成した Router をマウントします。
4.  **サイドバーへの追加**: `src/lib/modules/Sidebar.svelte` (またはナビゲーションコンポーネント) にリンクを追加します。

## ビルドとデプロイ

```bash
npm run build
# build/ ディレクトリに出力されます
node build
```

本番環境（Cloud Run）では、`Dockerfile` を使用してビルド・実行されます。
認証は前面の OAuth2 Proxy サイドカーが担当するため、アプリケーション単体で公開しないでください。
