import { json } from '@sveltejs/kit';
import * as gcp from '../../lib/gcp/billing';
import type { ModuleApi } from '../../lib/types/module';

export const GET: ModuleApi['GET'] = {
    'summary': async () => {
        const billing = await gcp.getBillingSummary();
        return json(billing);
    }
};
