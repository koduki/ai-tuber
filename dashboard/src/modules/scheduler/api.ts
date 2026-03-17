import { json } from '@sveltejs/kit';
import * as gcp from '../../gcpClient';

export const GET: Record<string, () => Promise<Response>> = {
    'index': async () => {
        const jobs = await gcp.getSchedulerJobs();
        return json(jobs);
    }
};

export const POST: Record<string, (url: URL) => Promise<Response>> = {
    'run': async (url: URL) => {
        const name = url.searchParams.get('name');
        if (!name) return json({ error: 'Job name is required' }, { status: 400 });
        await gcp.runSchedulerJob(name);
        return json({ message: `Job ${name} started` });
    }
};
