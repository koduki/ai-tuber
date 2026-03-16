import * as gcp from '$lib/gcpClient';
import { json } from '@sveltejs/kit';

export const GET = {
    index: async () => {
        try {
            const instances = await gcp.getComputeInstances();
            return json(instances);
        } catch (err: any) {
            return json({ error: err.message }, { status: 500 });
        }
    }
};
