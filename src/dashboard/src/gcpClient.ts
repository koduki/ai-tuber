/**
 * GCP API クライアント
 * SDK を活用し OpenTofu 管理下のリソース情報を取得
 */

import { CloudSchedulerClient } from '@google-cloud/scheduler';
import { WorkflowsClient } from '@google-cloud/workflows';
import { ServicesClient, JobsClient } from '@google-cloud/run';
import { InstancesClient } from '@google-cloud/compute';
import { CloudBuildClient } from '@google-cloud/cloudbuild';
import { BudgetServiceClient } from '@google-cloud/billing-budgets';
import { BigQuery } from '@google-cloud/bigquery';
import { config } from './config';

// クライアントの初期化
const scheduler = new CloudSchedulerClient();
const workflows = new WorkflowsClient();
const runServices = new ServicesClient();
const runJobs = new JobsClient();
const compute = new InstancesClient();
const cloudBuild = new CloudBuildClient();
const budgets = new BudgetServiceClient();
const bigquery = new BigQuery();

// ============================================================
// Cloud Scheduler
// ============================================================

interface SchedulerJob {
    name: string;
    displayName: string;
    lastStatus: string;
    lastRunTime: string;
    nextRunTime: string;
    region: string;
    state: string;
    description: string;
    schedule: string;
}

export async function getSchedulerJobs(): Promise<SchedulerJob[]> {
    const parent = `projects/${config.projectId}/locations/${config.region}`;
    const [jobs] = await scheduler.listJobs({ parent });

    return (jobs || []).map((job: any) => {
        const shortName = job.name?.split('/').pop() || '';
        return {
            name: shortName,
            displayName: shortName,
            lastStatus: mapSchedulerStatus(job.status),
            lastRunTime: formatTimestamp(job.status?.latestExecution?.scheduleTime || job.lastAttemptTime),
            nextRunTime: formatTimestamp(job.nextRunTime),
            region: config.region,
            state: job.state === 'ENABLED' ? '有効' : '無効',
            description: job.description || '',
            schedule: job.schedule || '',
        };
    });
}

export async function runSchedulerJob(jobName: string): Promise<void> {
    const name = `projects/${config.projectId}/locations/${config.region}/jobs/${jobName}`;
    await scheduler.runJob({ name });
}

function mapSchedulerStatus(status: any): string {
    if (!status) return '不明';

    // V2 API (Google Cloud Scheduler v1/v2 might have subtle differences in SDK)
    const state = status.latestExecution?.state;
    if (state) {
        if (state === 'SUCCEEDED') return '成功';
        if (state === 'FAILED') return '失敗';
        if (state === 'RUNNING') return '実行中';
    }

    // google.rpc.Status code mapping
    // code: 0 or {} usually means success in Proto3 JSON if lastAttemptTime exists
    if (status.code === 0 || (typeof status.code === 'undefined' && Object.keys(status).length === 0)) {
        return '成功';
    }

    return (status.code > 0) ? '失敗' : '不明';
}

// ============================================================
// Cloud Workflows
// ============================================================

interface WorkflowInfo {
    name: string;
    location: string;
    revision: string;
    created: string;
    updated: string;
    labels: string;
}

export async function getWorkflowInfo(): Promise<WorkflowInfo[]> {
    const parent = `projects/${config.projectId}/locations/${config.region}`;
    const [wfs] = await workflows.listWorkflows({ parent });

    return (wfs || []).map((wf: any) => {
        const shortName = wf.name?.split('/').pop() || '';
        const labels = wf.labels
            ? Object.entries(wf.labels).map(([k, v]) => `${k}: ${v}`).join(', ')
            : '';
        return {
            name: shortName,
            location: config.region,
            revision: wf.revisionId || '',
            created: formatTimestamp(wf.createTime),
            updated: formatTimestamp(wf.updateTime),
            labels,
        };
    });
}

interface WorkflowExecution {
    stepName: string;
    status: string;
    executionId: string;
    revision: string;
    created: string;
    started: string;
    ended: string;
}

// NOTE: Workflow Executions requires a separate REST API call or unofficial library
// as of current stable Node Cloud SDK, so fallback to fetch for executions
async function gcpFetch(url: string): Promise<any> {
    const { GoogleAuth } = await import('google-auth-library');
    const auth = new GoogleAuth({ scopes: ['https://www.googleapis.com/auth/cloud-platform'] });
    const client = await auth.getClient();
    const token = (await client.getAccessToken()).token;
    const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
    if (!res.ok) throw new Error(`Fetch ${url} failed: ${res.status}`);
    return res.json();
}

export async function getWorkflowExecutions(): Promise<WorkflowExecution[]> {
    const workflowName = config.resources.workflows.streamingPipeline;
    const parent = `projects/${config.projectId}/locations/${config.region}/workflows/${workflowName}`;
    const EXECUTIONS_API = 'https://workflowexecutions.googleapis.com/v1';

    try {
        const data = await gcpFetch(`${EXECUTIONS_API}/${parent}/executions?pageSize=4&orderBy=startTime desc`);
        const executions = data.executions || [];

        return executions.map((ex: any) => {
            const exId = ex.name?.split('/').pop() || '';
            const stepLabel = ex.status?.currentSteps?.[0]?.step || (ex.state === 'ACTIVE' ? 'executing' : 'end');

            return {
                stepName: stepLabel,
                status: mapExecutionStatus(ex.state),
                executionId: exId,
                revision: ex.workflowRevisionId || '',
                created: formatTimestamp(ex.createTime),
                started: formatTimestamp(ex.startTime),
                ended: formatTimestamp(ex.endTime),
                location: config.region,
            };
        });
    } catch (err) {
        console.error('Error fetching workflow executions:', err);
        return [];
    }
}

function mapExecutionStatus(state?: string): string {
    switch (state) {
        case 'SUCCEEDED': return '成功';
        case 'FAILED': return '失敗';
        case 'ACTIVE': return '実行中';
        case 'CANCELLED': return 'キャンセル';
        default: return '不明';
    }
}

// ============================================================
// Cloud Run (v2 Services)
// ============================================================

interface CloudRunService {
    name: string;
    status: string;
    region: string;
    authentication: string;
    ingress: string;
    uri: string;
}

export async function getCloudRunServices(): Promise<CloudRunService[]> {
    const parent = `projects/${config.projectId}/locations/${config.region}`;
    const [svcs] = await runServices.listServices({ parent });

    const managedNames = new Set(config.resources.cloudRunServices);
    const filtered = (svcs || []).filter(
        (svc: any) => managedNames.has(svc.name?.split('/').pop() || '')
    );

    return filtered.map((svc: any) => {
        const shortName = svc.name?.split('/').pop() || '';
        const conditions = svc.conditions || svc.status?.conditions || [];

        // デバッグ用: 必要に応じてコメントアウト
        // console.log(`Service: ${shortName}`, JSON.stringify(svc.status || svc, (k,v) => k === 'conditions' ? '[...]' : v));

        const isReady = conditions.some(
            (c: any) => c.type?.toLowerCase() === 'ready' &&
                (c.state === 'CONDITION_SUCCEEDED' || c.status === 'True' || c.state === 'SUCCEEDED')
        ) || (svc.terminalCondition?.type?.toLowerCase() === 'ready' &&
            (svc.terminalCondition?.state === 'CONDITION_SUCCEEDED' || svc.terminalCondition?.status === 'True'))
            || (svc.latestReadyRevisionName && !svc.reconciling);

        return {
            name: shortName,
            status: isReady ? '正常' : 'エラー',
            region: config.region,
            authentication: shortName === 'ai-tuber-tools-weather' ? '公開アクセス' : '認証が必要です',
            ingress: svc.ingress || 'すべて',
            uri: svc.uri || '',
        };
    });
}

// ============================================================
// Cloud Run (v2 Jobs)
// ============================================================

interface CloudRunJob {
    name: string;
    status: string;
    lastExecution: string;
    region: string;
    creator: string;
    trigger: string;
}

export async function getCloudRunJobs(): Promise<CloudRunJob[]> {
    const parent = `projects/${config.projectId}/locations/${config.region}`;
    const [jobs] = await runJobs.listJobs({ parent });

    const managedNames = new Set(config.resources.cloudRunJobs);
    const filtered = (jobs || []).filter(
        (job: any) => managedNames.has(job.name?.split('/').pop() || '')
    );

    return filtered.map((job: any) => {
        const shortName = job.name?.split('/').pop() || '';
        const latest = job.latestCreatedExecution;
        let status = '不明';
        if (latest) {
            if (latest.completionStatus === 'EXECUTION_SUCCEEDED' || latest.completionStatus === 'SUCCEEDED') {
                status = '完了';
            } else if (latest.completionStatus === 'EXECUTION_FAILED' || latest.completionStatus === 'FAILED') {
                status = '失敗';
            } else if (latest.createTime && !latest.completionTime) {
                status = '実行中';
            }
        }

        // 起点と作成者の判定
        const trigger = latest?.labels?.['run.googleapis.com/triggered-by'] || (shortName.includes('collector') ? 'Cloud Scheduler' : 'Manual');
        const creator = latest?.annotations?.['run.googleapis.com/creator'] || '';

        return {
            name: shortName,
            status,
            lastExecution: formatTimestamp(latest?.createTime),
            region: config.region,
            location: config.region,
            creator,
            trigger,
        };
    });
}

// ============================================================
// Compute Engine
// ============================================================

interface ComputeInstance {
    name: string;
    status: string;
    zone: string;
    internalIp: string;
    externalIp: string;
    description: string;
}

export async function getComputeInstances(): Promise<ComputeInstance[]> {
    const results: ComputeInstance[] = [];

    for (const instanceName of config.resources.computeInstances) {
        try {
            const [instance] = await compute.get({
                project: config.projectId,
                zone: config.zone,
                instance: instanceName,
            });
            const networkInterface = instance.networkInterfaces?.[0];
            results.push({
                name: instance.name || instanceName,
                status: mapComputeStatus(instance.status),
                zone: config.zone,
                internalIp: networkInterface?.networkIP ? `${networkInterface.networkIP} (nic0)` : '',
                externalIp: networkInterface?.accessConfigs?.[0]?.natIP ? `${networkInterface.accessConfigs[0].natIP} (nic0)` : '',
                description: instance.description || (instance.labels?.['purpose'] || 'Body 接続確認用'),
            });
        } catch (err) {
            results.push({ name: instanceName, status: '取得エラー', zone: config.zone, internalIp: '', externalIp: '', description: '' });
        }
    }
    return results;
}

function mapComputeStatus(status?: string | null): string {
    switch (status) {
        case 'RUNNING': return '稼働中';
        case 'TERMINATED': return '停止';
        case 'STAGING': return '起動中';
        default: return status || '不明';
    }
}

// ============================================================
// Cloud Build
// ============================================================

interface CloudBuild {
    id: string;
    status: string;
    region: string;
    source: string;
    ref: string;
    commit: string;
    triggerName: string;
}

export async function getCloudBuildHistory(): Promise<CloudBuild[]> {
    try {
        const [builds] = await cloudBuild.listBuilds({ projectId: config.projectId });
        return (builds || []).slice(0, 10).map((b: any) => {
            return {
                id: (b.id || '').substring(0, 8),
                fullId: b.id || '',
                status: mapBuildStatus(b.status),
                region: 'global',
                source: b.substitutions?._REPOSITORY || '',
                ref: b.source?.repoSource?.branchName || '',
                commit: (b.sourceProvenance?.resolvedRepoSource?.commitSha || '').substring(0, 8),
                triggerName: b.buildTriggerId || '',
                triggerId: b.buildTriggerId || '',
            };
        });
    } catch (err) {
        console.error('Error fetching build history:', err);
        return [];
    }
}

function mapBuildStatus(status?: string): string {
    switch (status) {
        case 'SUCCESS': return '成功';
        case 'FAILURE': return '失敗';
        case 'WORKING': return 'ビルド中';
        default: return status || '不明';
    }
}

// ============================================================
// Billing
// ============================================================

interface BillingSummary {
    monthlyCost: string;
    forecast: string;
    budget: string;
    trend: 'up' | 'down' | 'stable';
    currency: string;
    dailyCosts: { date: string, cost: number }[];
    serviceCosts: { name: string, cost: number }[];
}

export async function getBillingSummary(): Promise<BillingSummary> {
    try {
        // 今月のコスト計算 (BigQuery)
        const summaryQuery = `
            SELECT 
                SUM(cost) as total_cost,
                MIN(currency) as currency
            FROM \`${config.projectId}.${config.billing.dataset}.${config.billing.tableName}\`
            WHERE usage_start_time >= TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), MONTH)
        `;

        const dailyQuery = `
            SELECT 
                DATE(usage_start_time) as usage_date,
                SUM(cost) as daily_cost
            FROM \`${config.projectId}.${config.billing.dataset}.${config.billing.tableName}\`
            WHERE usage_start_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
            GROUP BY usage_date
            ORDER BY usage_date ASC
        `;

        const serviceQuery = `
            SELECT 
                service.description as service_name,
                SUM(cost) as service_cost
            FROM \`${config.projectId}.${config.billing.dataset}.${config.billing.tableName}\`
            WHERE usage_start_time >= TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), MONTH)
            GROUP BY service_name
            ORDER BY service_cost DESC
            LIMIT 5
        `;

        const [
            [summaryRows],
            [dailyRows],
            [serviceRows]
        ] = await Promise.all([
            bigquery.query({ query: summaryQuery }),
            bigquery.query({ query: dailyQuery }),
            bigquery.query({ query: serviceQuery })
        ]);

        const cost = summaryRows[0]?.total_cost || 0;
        const currency = summaryRows[0]?.currency || 'USD';

        // 予算取得
        const parent = `billingAccounts/${config.billing.accountId}`;
        const [budgetList] = await budgets.listBudgets({ parent });
        const budgetAmount = budgetList[0]?.amount?.specifiedAmount?.units || '0';

        return {
            monthlyCost: `$${cost.toFixed(2)}`,
            forecast: 'データ収束中...',
            budget: `$${budgetAmount}`,
            trend: 'stable',
            currency,
            dailyCosts: dailyRows.map((r: any) => ({ date: r.usage_date.value, cost: r.daily_cost })),
            serviceCosts: serviceRows.map((r: any) => ({ name: r.service_name, cost: r.service_cost })),
        };
    } catch (err: any) {
        console.error('billing query error:', err.message);
        return {
            monthlyCost: '$0.00',
            forecast: '不明',
            budget: '$0.00',
            trend: 'stable',
            currency: 'USD',
            dailyCosts: [],
            serviceCosts: [],
        };
    }
}

// ============================================================
// Overview
// ============================================================

export async function getOverview() {
    const [schedulerJobs, executions, services, jobs, instances, billing] = await Promise.all([
        getSchedulerJobs().catch(() => []),
        getWorkflowExecutions().catch(() => []),
        getCloudRunServices().catch(() => []),
        getCloudRunJobs().catch(() => []),
        getComputeInstances().catch(() => []),
        getBillingSummary().catch(() => ({ monthlyCost: '$0.00', budget: '$0.00', detail: 'データなし', currency: 'USD' })),
    ]);

    const schedulerOk = schedulerJobs.every(j => j.lastStatus === '成功');
    const workflowOk = (executions[0]?.status === '成功');

    return {
        schedulerHealth: { value: schedulerOk ? 'OK' : 'エラー', detail: schedulerOk ? '直近実行は成功' : '失敗あり' },
        workflowState: { value: workflowOk ? '正常' : 'エラー', detail: workflowOk ? '最新 execution は成功' : '以前の実行に失敗あり' },
        runningResources: { value: services.length + jobs.length + instances.length, detail: `Run ${services.length} / Job ${jobs.length} / VM ${instances.length}` },
        externalIps: { value: instances.filter(i => i.externalIp).length, detail: '確認用 IP あり' },
        billing: { value: (billing as any).monthlyCost, detail: `予算 ${(billing as any).budget} / ${(billing as any).currency}` },
    };
}

function formatTimestamp(ts?: any): string {
    if (!ts) return '';
    try {
        const d = (typeof ts === 'string') ? new Date(ts) : new Date(Number(ts.seconds || 0) * 1000);
        return d.toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' }).replace(/\//g, '/');
    } catch {
        return String(ts);
    }
}
