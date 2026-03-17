import { json, error } from '@sveltejs/kit';
import * as gcp from '../../lib/gcp/scheduler';
import type { ModuleApi } from '../../lib/types/module';

export const GET: ModuleApi['GET'] = {
    'jobs': async () => {
        const jobs = await gcp.getSchedulerJobs();
        return json(jobs);
    }
};

export const POST: ModuleApi['POST'] = {
    'run': async (url) => {
        const jobName = url?.searchParams.get('jobName');
        if (!jobName) throw error(400, 'jobName is required');
        await gcp.runSchedulerJob(jobName);
        return json({ success: true });
    }
};
