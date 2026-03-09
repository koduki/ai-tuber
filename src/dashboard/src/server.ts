/**
 * ダッシュボード Express サーバー
 * GCP API から取得したリソース情報を提供する
 */

import express from 'express';
import path from 'path';
import { config } from './config';
import * as gcp from './gcpClient';

const app = express();

// 静的ファイル配信
app.use(express.static(path.join(__dirname, '..', 'public')));

// ─── API エンドポイント ──────────────────────────────────

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

/** 設定情報 (フロントエンド用) */
app.get('/api/config', (_req, res) => {
    res.json({
        projectId: config.projectId,
        region: config.region,
        zone: config.zone,
    });
});

// ─── サーバー起動 ──────────────────────────────────────

app.listen(config.port, () => {
    console.log(`Dashboard server listening on port ${config.port}`);
});
