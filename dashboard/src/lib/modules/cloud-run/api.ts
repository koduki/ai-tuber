import * as gcp from '$lib/gcpClient';
import { json } from '@sveltejs/kit';

export const GET = {
    services: async () => {
        try {
            const services = await gcp.getCloudRunServices();
            return json(services);
        } catch (err: any) {
            return json({ error: err.message }, { status: 500 });
        }
    }
};
