/**
 * ダッシュボード Express サーバー (Modular IDP Version)
 */

import express from 'express';
import path from 'path';
import cookieSession from 'cookie-session';
import { config } from './config';
import { getOAuth2Client, checkUserPermission } from './core/auth';
import { loadModules, ModuleInfo } from './core/loader';

async function startServer() {
    const app = express();
    const oauth2Client = getOAuth2Client();

    // モジュールのロード
    const modulesDir = path.join(__dirname, 'modules');
    const modules = await loadModules(modulesDir);

    // セッション設定
    app.use(cookieSession({
        name: 'session',
        keys: [config.auth.sessionSecret],
        maxAge: 24 * 60 * 60 * 1000 // 24 hours
    }));

    // ─── 認証ミドルウェア ──────────────────────────────────

    const authMiddleware = async (req: express.Request, res: express.Response, next: express.NextFunction) => {
        if (!req.session?.tokens) {
            if (req.path.startsWith('/api/')) {
                return res.status(401).json({ error: 'Unauthorized' });
            }
            return res.redirect('/auth/login');
        }
        next();
    };

    // ─── 認証ルート ────────────────────────────────────

    app.get('/auth/login', (req, res) => {
        const authorizeUrl = oauth2Client.generateAuthUrl({
            access_type: 'offline',
            scope: ['https://www.googleapis.com/auth/userinfo.email', 'openid'],
        });
        res.redirect(authorizeUrl);
    });

    app.get('/auth/callback', async (req, res) => {
        const { code } = req.query;
        if (!code) return res.status(400).send('Code not found');

        try {
            const { tokens } = await oauth2Client.getToken(code as string);
            const ticket = await oauth2Client.verifyIdToken({
                idToken: tokens.id_token!,
                audience: config.auth.clientId,
            });
            const payload = ticket.getPayload();
            const email = payload?.email;

            if (!email) throw new Error('Email not found in token');

            const hasAccess = await checkUserPermission(email);
            if (!hasAccess) {
                return res.status(403).send(`Access Denied: ユーザー ${email} は権限を持っていません。`);
            }

            req.session!.tokens = tokens;
            req.session!.userEmail = email;

            res.redirect('/');
        } catch (err: any) {
            console.error('Auth error:', err.message);
            res.status(500).send('Authentication failed');
        }
    });

    app.get('/auth/logout', (req, res) => {
        req.session = null;
        res.send('Logged out');
    });

    // ─── API エンドポイント ──────────────────────────────────

    app.use('/api', authMiddleware);

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
            userEmail: req.session?.userEmail,
        });
    });

    // ─── 静的ファイル配信 ──────────────────────────────────

    // クライアントのビルドディレクトリ
    const clientDistPath = path.join(__dirname, '..', 'client', 'dist');
    const clientPublicPath = path.join(__dirname, '..', 'public'); // 互換性のため

    if (process.env.NODE_ENV === 'production') {
        app.use(authMiddleware, express.static(clientDistPath));
        app.get('*', authMiddleware, (req, res) => {
            res.sendFile(path.join(clientDistPath, 'index.html'));
        });
    } else {
        // 開発時は public ディレクトリまたは Vite Proxy を想定
        app.use(authMiddleware, express.static(clientPublicPath));
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
