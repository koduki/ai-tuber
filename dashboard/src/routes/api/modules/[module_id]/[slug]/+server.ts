import { error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

async function getModuleApi(module_id: string) {
    const apiModules = import.meta.glob(['/src/modules/*/api.ts', '!/src/modules/_*/**'], { eager: true });
    return apiModules[`/src/modules/${module_id}/api.ts`];
}

export const GET: RequestHandler = async ({ params }) => {
    const { module_id, slug } = params;
    const moduleApi: any = await getModuleApi(module_id);
    if (!moduleApi || !moduleApi.GET || !moduleApi.GET[slug]) throw error(404, 'GET Endpoint not found');
    return await moduleApi.GET[slug]();
};

export const POST: RequestHandler = async ({ params, url }) => {
    const { module_id, slug } = params;
    const moduleApi: any = await getModuleApi(module_id);
    if (!moduleApi || !moduleApi.POST || !moduleApi.POST[slug]) throw error(404, 'POST Endpoint not found');
    return await moduleApi.POST[slug](url);
};
