import { json } from '@sveltejs/kit';
import * as gcp from '../../gcpClient';

export const GET: Record<string, () => Promise<Response>> = {
    'index': async () => {
        const [workflows, executions] = await Promise.all([
            gcp.getWorkflowInfo(),
            gcp.getWorkflowExecutions(),
        ]);
        return json({ workflows, executions });
    }
};
