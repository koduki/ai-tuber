import { json } from '@sveltejs/kit';
import type { ModuleApi } from '../../lib/types/module';

// GCP クライアントが必要な場合:
// import * as gcp from '../../lib/gcp/run';

export const GET: ModuleApi['GET'] = {
    // /api/modules/{module-id}/index でアクセス可能
    'index': async () => {
        // TODO: データ取得ロジックを実装
        return json({ message: 'Hello from template' });
    }
};

// POST エンドポイントが必要な場合:
// export const POST: ModuleApi['POST'] = {
//     'action': async (url) => {
//         const param = url?.searchParams.get('param');
//         return json({ result: 'ok' });
//     }
// };
