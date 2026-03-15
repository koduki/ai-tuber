---
name: dashboard-idp-management
description: Dashboard IDP (Internal Developer Platform) の管理、改修、および新機能（モジュール）の追加を行うためのスキル。
---

# Dashboard IDP Management Skill

このスキルは、AI Tuber プラットフォームのダッシュボード（IDP）を、AIが自律的に拡張・維持するためのガイドラインと手順を提供します。

## 1. フレームワークの概要

ダッシュボードは **Vite + React (Frontend)** と **Express (Backend)** で構成されるモジュール型フレームワークです。
「機能ごとのディレクトリ」を作成して配置することで、システムが自律的にスキャンして統合します。
- **Backend/Metadata**: `dashboard/src/modules/`
- **Frontend**: `dashboard/client/src/modules/`


## 2. モジュールの標準構造

新しい機能を追加する場合、`dashboard/src/modules/{module-id}/` を作成し、以下のファイルを配置します。

### Backend: `api.ts`
GCP SDK 等を使用してデータを取得・操作する Express Router を定義します。
```typescript
import { Router } from 'express';
const router = Router();
router.get('/data', async (req, res) => { /* ... */ });
export default router;
```

### Frontend: `View.tsx`
React コンポーネントを定義します。UIの可読性を高めるため、可能な限り標準的な UI ライブラリを使用してください。
```tsx
import React from 'react';
export const View = () => {
    return <div>新しい機能の画面</div>;
};
```

### Metadata: `index.ts`
モジュールのメタデータをエクスポートします。
```typescript
export const metadata = {
    id: 'storage',
    title: 'GCS Management',
    icon: 'HardDrive', // Lucide アイコン名
    priority: 10
};
```

## 3. 拡張ワークフロー

AIが新しい機能（例: Cloud Logging 閲覧）を追加する際の手順：

1.  **要件定義**: `gcpClient.ts` に必要な GCP API 呼び出しがあるか確認し、なければ追加する。
2.  **フォルダ作成**: 
    - `dashboard/src/modules/logging/` (Backend)
    - `dashboard/client/src/modules/logging/` (Frontend)
3.  **Backend実装**: `api.ts`, `index.ts` を作成。
4.  **Frontend実装**: `View.tsx` を作成。
5.  **検証**: ローカル環境で `npm run dev` し、新しいタブが出現し、正しくデータが表示されるか確認する。


## 4. インフラ情報の参照と取得

AIがダッシュボードを拡張する際、既存のインフラ構成を正確に把握するために以下の手段を活用してください。

### OpenTofu (IaC) の参照
`/app/opentofu/` ディレクトリ配下の `.tf` ファイルを参照することで、現在のリソース定義、IAMロール、環境変数、およびサービス間の依存関係を確認できます。
- **リソース構成**: `cloudrun.tf`, `compute.tf` など
- **権限管理**: `iam.tf`

### gcloud コマンドによる動的情報の取得
静的な定義だけでは不十分な場合、`run_command` を使用して `gcloud` コマンドを実行し、リアルタイムのステータスや設定を調査してください。
- **Service/Job の詳細**: `gcloud run services describe {NAME}`
- **ビルドステータス**: `gcloud builds list --limit=5`
- **権限確認**: `gcloud projects get-iam-policy {PROJECT_ID}`

## 5. 設計原則

-   **AI可読性の優先**: 複雑な抽象化よりも、一目で理解できる明示的な記述を好みます。
-   **独立性**: 各モジュールは他のモジュールに依存せず、単体で動作・完結するように設計します。
-   **GCPネイティブ**: 前提として Cloud Run にデプロイされるため、認証や環境変数はプラットフォームの仕組みを最大限活用します。
-   **事実に基づく拡張**: 推測でコードを書かず、OpenTofu や gcloud から得られた「事実（Source of Truth）」に基づいて実装を行います。
