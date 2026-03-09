/**
 * GCP API クライアント
 * SDK を活用し OpenTofu 管理下のリソース情報を取得
 */

import { CloudSchedulerClient } from '@google-cloud/scheduler';
import { WorkflowsClient } from '@google-cloud/workflows';
import { ServicesClient, JobsClient } from '@google-cloud/run';
import { InstancesClient } from '@google-cloud/compute';
import { CloudBuildClient } from '@google-cloud/cloudbuild';
import { config } from './config';

// クライアントの初期化
const scheduler = new CloudSchedulerClient();
const workflows = new WorkflowsClient();
const runServices = new ServicesClient();
const runJobs = new JobsClient();
const compute = new InstancesClient();
const cloudBuild = new CloudBuildClient();

// ============================================================
// Cloud Scheduler
// ============================================================

interface SchedulerJob {
    name: string;
    displayName: string;
    lastStatus: string;
    region: string;
    state: string;
    description: string;
    schedule: string;
    target: string;
}

export async function getSchedulerJobs(): Promise<SchedulerJob[]> {
    const parent = `projects/${config.projectId}/locations/${config.region}`;
    const [jobs] = await scheduler.listJobs({ parent });

    return (jobs || []).map((job: any) => {
        const shortName = job.name?.split('/').pop() || '';
        return {
            name: shortName,
            displayName: shortName,
            lastStatus: mapSchedulerStatus(job.status?.latestExecution?.state),
            region: config.region,
            state: job.state === 'ENABLED' ? '有効' : '無効',
            description: job.description || '',
            schedule: job.schedule || '',
            target: job.httpTarget?.uri || job.pubsubTarget?.topicName || '',
        };
    });
}

function mapSchedulerStatus(state?: string): string {
    switch (state) {
        case 'SUCCEEDED': return '成功';
        case 'FAILED': return '失敗';
        case 'RUNNING': return '実行中';
        default: return '不明';
    }
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
        const data = await gcpFetch(`${EXECUTIONS_API}/${parent}/executions?pageSize=10&orderBy=startTime desc`);
        const executions = data.executions || [];

        return executions.map((ex: any) => {
            const exId = ex.name?.split('/').pop() || '';
            return {
                stepName: ex.workflowRevisionId ? 'end' : 'executing',
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
        const isReady = svc.conditions?.some(
            (c: any) => c.type === 'Ready' && c.state === 'CONDITION_SUCCEEDED'
        );
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
        return {
            name: shortName,
            status: job.latestCreatedExecution?.completionTime ? '完了' : '不明',
            lastExecution: formatTimestamp(job.latestCreatedExecution?.createTime),
            region: config.region,
            location: config.region,
            creator: '',
            trigger: 'OpenTofu',
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
                description: 'Body 接続確認用',
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
// Overview
// ============================================================

export async function getOverview() {
    const [schedulerJobs, executions, services, jobs, instances] = await Promise.all([
        getSchedulerJobs().catch(() => []),
        getWorkflowExecutions().catch(() => []),
        getCloudRunServices().catch(() => []),
        getCloudRunJobs().catch(() => []),
        getComputeInstances().catch(() => []),
    ]);

    const schedulerOk = schedulerJobs.every(j => j.lastStatus === '成功');
    const workflowOk = (executions[0]?.status === '成功');

    return {
        schedulerHealth: { value: schedulerOk ? 'OK' : 'エラー', detail: schedulerOk ? '直近実行は成功' : '失敗あり' },
        workflowState: { value: workflowOk ? '正常' : 'エラー', detail: workflowOk ? '最新 execution は成功' : '以前の実行に失敗あり' },
        runningResources: { value: services.length + jobs.length + instances.length, detail: `Run ${services.length} / Job ${jobs.length} / VM ${instances.length}` },
        externalIps: { value: instances.filter(i => i.externalIp).length, detail: '確認用 IP あり' },
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
