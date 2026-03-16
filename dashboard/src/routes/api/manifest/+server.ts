import { json } from '@sveltejs/kit';

export async function GET() {
    const modules = import.meta.glob('/src/lib/modules/*/metadata.ts', { eager: true });
    
    const manifest = Object.entries(modules).map(([path, mod]: [string, any]) => {
        const parts = path.split('/');
        const id = parts[parts.length - 2];
        return {
            ...mod.metadata,
            id
        };
    }).sort((a, b) => (a.priority || 100) - (b.priority || 100));

    return json(manifest);
}
