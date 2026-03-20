import fs from 'fs';
import path from 'path';
import { Router } from 'express';

export interface ModuleMetadata {
    id: string;
    title: string;
    icon: string;
    priority?: number;
}

export interface ModuleInfo {
    metadata: ModuleMetadata;
    router?: Router;
    viewPath?: string;
}

/**
 * modules/ ディレクトリをスキャンし、APIとメタデータをロードする
 */
export async function loadModules(modulesDir: string): Promise<ModuleInfo[]> {
    const modules: ModuleInfo[] = [];
    
    if (!fs.existsSync(modulesDir)) {
        return modules;
    }

    const dirs = fs.readdirSync(modulesDir).filter(f => 
        fs.statSync(path.join(modulesDir, f)).isDirectory()
    );

    for (const id of dirs) {
        const modulePath = path.join(modulesDir, id);
        
        try {
            // index.ts (または .js) からメタデータを取得
            // 動的インポートを使用して TypeScript ファイルを直接読み込む (tsx/ts-node前提)
            const indexModule = await import(path.join(modulePath, 'index'));
            const metadata: ModuleMetadata = { ...indexModule.metadata, id };

            // api.ts から Router を取得
            let router: Router | undefined;
            const apiFilePath = path.join(modulePath, 'api.ts');
            if (fs.existsSync(apiFilePath)) {
                const apiModule = await import(path.join(modulePath, 'api'));
                router = apiModule.default;
            }

            modules.push({ metadata, router });
            console.log(`Loader: Loaded module "${metadata.title}" (${id})`);
        } catch (err: any) {
            console.error(`Loader: Failed to load module "${id}":`, err.message);
        }
    }

    // priority 順にソート
    return modules.sort((a, b) => (a.metadata.priority || 100) - (b.metadata.priority || 100));
}
