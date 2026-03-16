import * as gcp from '$lib/gcpClient';
import { json } from '@sveltejs/kit';

export const GET = {
    index: async () => {
        try {
            const builds = await gcp.getCloudBuildHistory();
            return json(builds);
        } catch (err: any) {
            return json({ error: err.message }, { status: 500 });
        }
    }
};
