import { json } from '@sveltejs/kit';
import * as gcp from '../../gcpClient';

export const GET: Record<string, () => Promise<Response>> = {
    'index': async () => {
        const builds = await gcp.getCloudBuildHistory();
        return json(builds);
    }
};
