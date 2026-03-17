import { json } from '@sveltejs/kit';
import * as gcp from '../../lib/gcp/run';
import type { ModuleApi } from '../../lib/types/module';

export const GET: ModuleApi['GET'] = {
    'services': async () => {
        const services = await gcp.getCloudRunServices();
        return json(services);
    },
    'jobs': async () => {
        const jobs = await gcp.getCloudRunJobs();
        return json(jobs);
    }
};
