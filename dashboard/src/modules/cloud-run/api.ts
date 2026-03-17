import { json } from '@sveltejs/kit';
import * as gcp from '../../gcpClient';

export const GET: Record<string, () => Promise<Response>> = {
    'services': async () => {
        const services = await gcp.getCloudRunServices();
        return json(services);
    },
    'jobs': async () => {
        const jobs = await gcp.getCloudRunJobs();
        return json(jobs);
    }
};
