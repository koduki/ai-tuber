import * as gcp from '$lib/gcpClient';
import { json } from '@sveltejs/kit';

export const GET = {
    all: async () => {
        try {
            const [workflows, executions] = await Promise.all([
                gcp.getWorkflowInfo(),
                gcp.getWorkflowExecutions()
            ]);
            return json({ workflows, executions });
        } catch (err: any) {
            return json({ error: err.message }, { status: 500 });
        }
    }
};
