import { json } from '@sveltejs/kit';
import * as gcp from '../../lib/gcp/compute';
import type { ModuleApi } from '../../lib/types/module';

export const GET: ModuleApi['GET'] = {
    'instances': async () => {
        const instances = await gcp.getComputeInstances();
        return json(instances);
    }
};
