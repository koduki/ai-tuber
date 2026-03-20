import { json } from '@sveltejs/kit';
import { config } from '../../../config';

export async function GET() {
    return json({
        projectId: config.projectId,
        region: config.region,
        zone: config.zone
    });
}
