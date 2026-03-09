/**
 * ダッシュボード設定
 * 環境変数と OpenTofu リソース名の定数管理
 */

export const config = {
    // GCP プロジェクト設定
    projectId: process.env.GCP_PROJECT_ID || 'ren-studio-ai',
    region: process.env.GCP_REGION || 'asia-northeast1',
    zone: process.env.GCP_ZONE || 'asia-northeast1-a',

    // サーバー設定
    port: parseInt(process.env.PORT || '8080', 10),

    // OpenTofu で管理されるリソース名
    resources: {
        // Cloud Scheduler (scheduler.tf)
        scheduler: {
            workflowTrigger: 'ai-tuber-workflow-daily',
        },

        // Cloud Workflows (scheduler.tf)
        workflows: {
            streamingPipeline: 'ai-tuber-streaming-pipeline',
        },

        // Cloud Run Services (cloudrun.tf)
        cloudRunServices: [
            'ai-tuber-healthcheck-proxy',
            'ai-tuber-tools-weather',
        ],

        // Cloud Run Jobs (cloudrun.tf)
        cloudRunJobs: [
            'ai-tuber-saint-graph',
            'ai-tuber-news-collector',
        ],

        // Compute Engine (compute.tf)
        computeInstances: [
            'ai-tuber-body-node',
        ],

        // Cloud Build Triggers (cloudbuild.tf)
        cloudBuildTriggers: [
            'ai-tuber-saint-graph',
            'ai-tuber-body',
            'ai-tuber-news-collector',
            'ai-tuber-tools-weather',
            'ai-tuber-mind-data-sync',
        ],
    },
} as const;
