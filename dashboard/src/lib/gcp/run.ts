import { ServicesClient, JobsClient } from '@google-cloud/run';
import { config } from '../../config';

const runServices = new ServicesClient();
const runJobs = new JobsClient();

export interface CloudRunService {
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

    const services = svcs || [];
    // 各サービスの IAM ポリシーを並列で取得して、公開アクセス（allUsers が invoker 権限を持っているか）を判定する
    const authStatuses = await Promise.all(
        services.map(async (svc: any) => {
            try {
                const [policy] = await runServices.getIamPolicy({ resource: svc.name });
                const isPublic = (policy.bindings || []).some(
                    (b: any) => (b.role === 'roles/run.invoker' || b.role === 'roles/viewer') &&
                        (b.members || []).some((m: string) => m === 'allUsers' || m === 'allAuthenticatedUsers')
                );
                return isPublic ? '公開アクセス' : '認証が必要です';
            } catch (err) {
                console.error(`Error getting IAM policy for ${svc.name}:`, err);
                return '不明';
            }
        })
    );

    return services.map((svc: any, index: number) => {
        const shortName = svc.name?.split('/').pop() || '';
        const conditions = svc.conditions || svc.status?.conditions || [];

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
            authentication: authStatuses[index],
            ingress: svc.ingress || 'すべて',
            uri: svc.uri || '',
        };
    });
}

export interface CloudRunJob {
    name: string;
    status: string;
    lastExecution: string;
    region: string;
    creator: string;
    trigger: string;
}

export async function getCloudRunJobs(): Promise<CloudRunJob[]> {
    const { formatTimestamp } = await import('./auth');
    const parent = `projects/${config.projectId}/locations/${config.region}`;
    const [jobs] = await runJobs.listJobs({ parent });

    return (jobs || []).map((job: any) => {
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

        const trigger = latest?.labels?.['run.googleapis.com/triggered-by'] || 'Manual';
        const creator = latest?.annotations?.['run.googleapis.com/creator'] || '';

        return {
            name: shortName,
            status,
            lastExecution: formatTimestamp(latest?.createTime),
            region: config.region,
            creator,
            trigger,
        };
    });
}
