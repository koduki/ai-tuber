/**
 * ダッシュボード Express サーバー
 * GCP API から取得したリソース情報を提供する
 */

import express from 'express';
import path from 'path';
import cookieSession from 'cookie-session';
import { OAuth2Client } from 'google-auth-library';
import { config } from './config';
import * as gcp from './gcpClient';

const app = express();
const oauth2Client = new OAuth2Client(
    config.auth.clientId,
    config.auth.clientSecret,
    config.auth.redirectUri
);

// セッション設定
app.use(cookieSession({
    name: 'session',
    keys: [config.auth.sessionSecret],
    maxAge: 24 * 60 * 60 * 1000 // 24 hours
}));

// ─── 認証ミドルウェア ──────────────────────────────────

const authMiddleware = async (req: express.Request, res: express.Response, next: express.NextFunction) => {
    // ローカル開発環境（GCP_PROJECT_ID がデフォルトの場合）はスキップする設定も可能だが
    // 基本は認証を強制する
    if (!req.session?.tokens) {
        if (req.path.startsWith('/api/')) {
            return res.status(401).json({ error: 'Unauthorized' });
        }
        return res.redirect('/auth/login');
    }
    next();
};

// ─── 認証ルート ────────────────────────────────────

/** ログイン画面 (または自動リダイレクト) */
app.get('/auth/login', (req, res) => {
    const authorizeUrl = oauth2Client.generateAuthUrl({
        access_type: 'offline',
        scope: ['https://www.googleapis.com/auth/userinfo.email', 'openid'],
    });
    res.redirect(authorizeUrl);
});

/** OAuth 回収 */
app.get('/auth/callback', async (req, res) => {
    const { code } = req.query;
    if (!code) return res.status(400).send('Code not found');

    try {
        const { tokens } = await oauth2Client.getToken(code as string);
        
        // ID トークンからメールアドレスを取得
        const ticket = await oauth2Client.verifyIdToken({
            idToken: tokens.id_token!,
            audience: config.auth.clientId,
        });
        const payload = ticket.getPayload();
        const email = payload?.email;

        if (!email) throw new Error('Email not found in token');

        // IAM 権限チェック (gcpClient に実装)
        const hasAccess = await gcp.checkUserPermission(email);
        if (!hasAccess) {
            return res.status(403).send(`Access Denied: ユーザー ${email} はこのプロジェクトの閲覧権限を持っていません。`);
        }

        // セッション保存
        req.session!.tokens = tokens;
        req.session!.userEmail = email;

        res.redirect('/');
    } catch (err: any) {
        console.error('Auth error:', err.message);
        res.status(500).send('Authentication failed');
    }
});

/** ログアウト */
app.get('/auth/logout', (req, res) => {
    req.session = null;
    res.send('Logged out');
});

// 静的ファイル配信 (未認証でもアクセス可能にする必要があるかもしれないが、基本は index.html も守る)
app.use(authMiddleware, express.static(path.join(__dirname, '..', 'public')));

// ─── API エンドポイント ──────────────────────────────────

// すべての API に認証を適用
app.use('/api', authMiddleware);

/** 概要サマリー */
app.get('/api/overview', async (_req, res) => {
    try {
        const overview = await gcp.getOverview();
        res.json(overview);
    } catch (err: any) {
        console.error('overview error:', err.message);
        res.status(500).json({ error: err.message });
    }
});

/** Cloud Scheduler ジョブ一覧 */
app.get('/api/scheduler', async (_req, res) => {
    try {
        const jobs = await gcp.getSchedulerJobs();
        res.json(jobs);
    } catch (err: any) {
        console.error('scheduler error:', err.message);
        res.status(500).json({ error: err.message });
    }
});

/** Scheduler ジョブ強制実行 */
app.post('/api/scheduler/:name/run', async (req, res) => {
    try {
        const name = req.params.name;
        await gcp.runSchedulerJob(name);
        res.json({ message: `Job ${name} started` });
    } catch (err: any) {
        console.error('run scheduler error:', err.message);
        res.status(500).json({ error: err.message });
    }
});

/** Workflow + Executions */
app.get('/api/workflows', async (_req, res) => {
    try {
        const [workflows, executions] = await Promise.all([
            gcp.getWorkflowInfo(),
            gcp.getWorkflowExecutions(),
        ]);
        res.json({ workflows, executions });
    } catch (err: any) {
        console.error('workflows error:', err.message);
        res.status(500).json({ error: err.message });
    }
});

/** Cloud Run サービス + ジョブ */
app.get('/api/services', async (_req, res) => {
    try {
        const [services, jobs] = await Promise.all([
            gcp.getCloudRunServices(),
            gcp.getCloudRunJobs(),
        ]);
        res.json({ services, jobs });
    } catch (err: any) {
        console.error('services error:', err.message);
        res.status(500).json({ error: err.message });
    }
});

/** Compute Engine インスタンス */
app.get('/api/compute', async (_req, res) => {
    try {
        const instances = await gcp.getComputeInstances();
        res.json(instances);
    } catch (err: any) {
        console.error('compute error:', err.message);
        res.status(500).json({ error: err.message });
    }
});

/** Cloud Build 履歴 */
app.get('/api/builds', async (_req, res) => {
    try {
        const builds = await gcp.getCloudBuildHistory();
        res.json(builds);
    } catch (err: any) {
        console.error('builds error:', err.message);
        res.status(500).json({ error: err.message });
    }
});

/** Billing 情報 */
app.get('/api/billing', async (_req, res) => {
    try {
        const billing = await gcp.getBillingSummary();
        res.json(billing);
    } catch (err: any) {
        console.error('billing error:', err.message);
        res.status(500).json({ error: err.message });
    }
});

/** 設定情報 (フロントエンド用) */
app.get('/api/config', (_req, res) => {
    res.json({
        projectId: config.projectId,
        region: config.region,
        zone: config.zone,
        userEmail: (_req as any).session?.userEmail,
    });
});

// ─── サーバー起動 ──────────────────────────────────────

app.listen(config.port, () => {
    console.log(`Dashboard server listening on port ${config.port}`);
});
