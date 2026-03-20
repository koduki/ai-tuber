import { json } from '@sveltejs/kit';
import * as gcp from '../../lib/gcp/workflows';
import type { ModuleApi } from '../../lib/types/module';

export const GET: ModuleApi['GET'] = {
    'info': async () => {
        const info = await gcp.getWorkflowInfo();
        return json(info);
    },
    'executions': async () => {
        const executions = await gcp.getWorkflowExecutions();
        return json(executions);
    }
};
