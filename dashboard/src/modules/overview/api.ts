import { json } from '@sveltejs/kit';
import * as gcp from '../../gcpClient';

export const GET: Record<string, () => Promise<Response>> = {
    'index': async () => {
        const overview = await gcp.getOverview();
        return json(overview);
    }
};
