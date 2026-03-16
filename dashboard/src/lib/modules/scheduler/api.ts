import * as gcp from '$lib/gcpClient';
import { json } from '@sveltejs/kit';

export const GET = {
    index: async () => {
        try {
            const jobs = await gcp.getSchedulerJobs();
            return json(jobs);
        } catch (err: any) {
            return json({ error: err.message }, { status: 500 });
        }
    }
};

export const POST = {
    run: async (url: URL) => {
        const jobName = url.searchParams.get('jobName');
        if (!jobName) return json({ error: 'Missing jobName' }, { status: 400 });
        try {
            await gcp.runSchedulerJob(jobName);
            return json({ success: true });
        } catch (err: any) {
            return json({ error: err.message }, { status: 500 });
        }
    }
};
