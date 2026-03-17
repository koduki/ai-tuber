import { json } from '@sveltejs/kit';
import * as gcp from '../../gcpClient';

export const GET: Record<string, () => Promise<Response>> = {
    'summary': async () => {
        const billing = await gcp.getBillingSummary();
        return json(billing);
    }
};
