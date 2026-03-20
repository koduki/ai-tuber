---
name: dashboard-idp-management
description: Dashboard IDP (Internal Developer Platform) の管理、改修、および新機能（モジュール）の追加を行うためのスキル。
---

# Dashboard IDP Management Skill

このスキルは、AI Tuber プラットフォームのダッシュボード（IDP）を、AIが自律的に拡張・維持するためのガイドラインと手順を提供します。

## 1. フレームワークの概要

ダッシュボードは **SvelteKit** をベースとしたモジュール型フレームワークです。
各機能は `dashboard/src/modules/[module_id]/` ディレクトリに集約されており、システムがこれを動的に読み込み、サイドバーのナビゲーションや API ルートを自動生成します。

- **技術スタック**: SvelteKit, TypeScript, TailwindCSS, Lucide Icons
- **モジュール配置**: `dashboard/src/modules/`

## 2. モジュールの標準構造

新しい機能を追加する場合、`dashboard/src/modules/{module-id}/` を作成し、以下のファイルを配置します。

### Backend API: `api.ts`
SvelteKit のランタイムから呼び出される API エンドポイントを定義します。
`GET` または `POST` オブジェクトをエクスポートし、その中に関数を定義します。
関数名は URL の `slug` 部分（`/api/modules/{module-id}/{slug}`）として公開されます。

```typescript
import { json } from '@sveltejs/kit';
import * as gcp from '../../gcpClient';

export const GET: Record<string, () => Promise<Response>> = {
    'index': async () => {
        const data = await gcp.someFunction();
        return json(data);
    }
};
```

### Frontend View: `View.svelte`
Svelte 5 コンポーネントを定義します。TailwindCSS を使用して、Google Cloud Console に近い清潔な UI を構築してください。

```svelte
<script lang="ts">
    import { onMount } from 'svelte';
    let data = $state(null);

    onMount(async () => {
        const res = await fetch('/api/modules/my-module/index');
        data = await res.json();
    });
</script>

<div class="p-4 bg-white border border-google-gray-300 rounded-lg">
    <h2 class="text-sm font-medium">機能タイトル</h2>
    <!-- UI の実装 -->
</div>
```

### Metadata: `index.ts`
モジュールのメタデータをエクスポートします。サイドバーの表示に使用されます。

```typescript
export const metadata = {
    title: '機能名',
    icon: 'Activity', // Lucide-Svelte のアイコン名
    priority: 100    // 数値が小さいほど上位に表示
};
```

## 3. 拡張ワークフロー

AIが新しい機能を追加する際の手順：

1.  **GCP Client の確認**: `dashboard/src/gcpClient.ts` に必要な GCP API 呼び出しがあるか確認し、なければ追加する。
2.  **フォルダ作成**: `dashboard/src/modules/{module_id}/` を作成。
3.  **Metadata 実装**: `index.ts` を作成し、適切なアイコンとタイトルを設定。
4.  **Backend API 実装**: `api.ts` を作成。複雑なデータ取得は `gcpClient.ts` に委譲すること。
5.  **Frontend View 実装**: `View.svelte` を作成。既存のモジュール（例: `cloud-run/View.svelte`）を参考に、Google 風のデザイン（GCP Blue, Gray, Green 等）を維持する。
6.  **検証**: `npm run dev` で起動し、サイドバーにメニューが出現し、正しくデータが表示されるか確認する。

## 4. インフラ情報の参照と取得

### OpenTofu (IaC) の参照
`/app/opentofu/` ディレクトリ配下の `.tf` ファイルを参照することで、現在のリソース定義や環境変数を確認できます。

### gcloud コマンドによる動的情報の取得
`run_command` を使用して `gcloud` コマンドを実行し、リアルタイムのステータスや設定を調査してください。
- **Service/Job の詳細**: `gcloud run services describe {NAME}`
- **ビルドステータス**: `gcloud builds list --limit=5`

## 5. 設計原則と注意点

-   **ESM (ES Modules) 準拠**: `require()` は使用不可。必ず `import` を使用してください。
-   **GCP SDK の ESM 問題**: `@google-cloud/workflows` 等の SDK は ESM 環境でエラーになる場合があります。その際は `src/gcpClient.ts` 内の `gcpFetch` を使用した REST API 呼び出しに切り替えてください。
-   **TailwindCSS の活用**: インラインスタイルや外部 CSS は避け、TailwindCSS のユーティリティクラス（`text-google-blue`, `bg-google-gray-50` 等）を使用してください。
-   **認証の前提**: ユーザー情報は OAuth2 Proxy からのヘッダー（`X-Forwarded-Email`）を介して `hooks.server.ts` で処理されます。
-   **事実に基づく拡張**: 推測でコードを書かず、OpenTofu や gcloud から得られた「事実」に基づいて実装してください。

