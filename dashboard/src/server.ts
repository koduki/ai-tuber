/**
 * ダッシュボード Express サーバー (Modular IDP Version)
 * 認証はサイドカー (OAuth2 Proxy) で行うため、ここではアプリロジックに集中する
 */

import express from 'express';
import path from 'path';
import { config } from './config';
import { loadModules } from './core/loader';

async function startServer() {
    const app = express();

    // モジュールのロード
    const modulesDir = path.join(__dirname, 'modules');
    const modules = await loadModules(modulesDir);

    // ─── ミドルウェア ──────────────────────────────────

    // OAuth2 Proxy から渡されるヘッダーを取得するミドルウェア
    app.use((req, res, next) => {
        const userEmail = req.header('X-Forwarded-Email') || req.header('X-Auth-Request-Email');
        if (userEmail) {
            (req as any).userEmail = userEmail;
        }
        next();
    });

    // ─── API エンドポイント ──────────────────────────────────

    // モジュール一覧 (Manifest)
    app.get('/api/manifest', (req, res) => {
        res.json(modules.map(m => m.metadata));
    });

    // 各モジュールの API マウント
    for (const mod of modules) {
        if (mod.router) {
            app.use(`/api/modules/${mod.metadata.id}`, mod.router);
            console.log(`Server: Mounted API for module "${mod.metadata.id}" at /api/modules/${mod.metadata.id}`);
        }
    }

    // 共通設定 API
    app.get('/api/config', (req, res) => {
        res.json({
            projectId: config.projectId,
            region: config.region,
            zone: config.zone,
            userEmail: (req as any).userEmail,
        });
    });

    // ─── 静的ファイル配信 ──────────────────────────────────

    // クライアントのビルドディレクトリ
    const clientDistPath = path.join(__dirname, '..', 'client', 'dist');
    const clientPublicPath = path.join(__dirname, '..', 'public'); // 互換性のため

    if (process.env.NODE_ENV === 'production') {
        app.use(express.static(clientDistPath));
        app.get('*', (req, res) => {
            res.sendFile(path.join(clientDistPath, 'index.html'));
        });
    } else {
        // 開発時は public ディレクトリまたは Vite Proxy を想定
        app.use(express.static(clientPublicPath));
    }

    // ─── サーバー起動 ──────────────────────────────────────

    app.listen(config.port, () => {
        console.log(`Modular Dashboard server listening on port ${config.port}`);
    });
}

startServer().catch(err => {
    console.error('Failed to start server:', err);
    process.exit(1);
});
