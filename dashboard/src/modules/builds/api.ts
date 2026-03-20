import { json } from '@sveltejs/kit';
import * as gcp from '../../lib/gcp/build';
import type { ModuleApi } from '../../lib/types/module';

export const GET: ModuleApi['GET'] = {
    'history': async () => {
        const history = await gcp.getCloudBuildHistory();
        return json(history);
    }
};
