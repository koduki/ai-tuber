import * as gcp from '$lib/gcpClient';
import { json } from '@sveltejs/kit';

export const GET = {
    summary: async () => {
        try {
            const billing = await gcp.getBillingSummary();
            return json(billing);
        } catch (err: any) {
            return json({ error: err.message }, { status: 500 });
        }
    }
};
