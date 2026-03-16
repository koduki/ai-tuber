import * as gcp from '$lib/gcpClient';
import { json } from '@sveltejs/kit';

export const GET = {
    index: async () => {
        try {
            const overview = await gcp.getOverview();
            return json(overview);
        } catch (err: any) {
            return json({ error: err.message }, { status: 500 });
        }
    }
};
