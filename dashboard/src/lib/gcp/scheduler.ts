import { CloudSchedulerClient } from '@google-cloud/scheduler';
import { config } from '../../config';

const scheduler = new CloudSchedulerClient();

export interface SchedulerJob {
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
    const { formatTimestamp } = await import('./auth');
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
    const state = status.latestExecution?.state;
    if (state) {
        if (state === 'SUCCEEDED') return '成功';
        if (state === 'FAILED') return '失敗';
        if (state === 'RUNNING') return '実行中';
    }
    if (status.code === 0 || (typeof status.code === 'undefined' && Object.keys(status).length === 0)) {
        return '成功';
    }
    return (status.code > 0) ? '失敗' : '不明';
}
