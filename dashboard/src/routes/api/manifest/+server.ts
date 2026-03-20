import { json } from '@sveltejs/kit';
import type { ModuleMetadata, ModuleManifest } from '../../../lib/types/module';

export async function GET() {
    const modules = import.meta.glob(['/src/modules/*/index.ts', '!/src/modules/_*/**'], { eager: true });
    
    const manifest: ModuleManifest[] = Object.entries(modules).map(([path, mod]: [string, any]) => {
        const parts = path.split('/');
        const id = parts[parts.length - 2];
        const metadata = mod.metadata as ModuleMetadata;
        return {
            ...metadata,
            id
        };
    }).sort((a, b) => (a.priority || 100) - (b.priority || 100));

    return json(manifest);
}
