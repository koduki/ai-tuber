import { config } from '../../config';
import { gcpFetch, formatTimestamp } from './auth';

export interface WorkflowInfo {
    name: string;
    location: string;
    revision: string;
    created: string;
    updated: string;
    labels: string;
}

export async function getWorkflowInfo(): Promise<WorkflowInfo[]> {
    const parent = `projects/${config.projectId}/locations/${config.region}`;
    const WORKFLOWS_API = 'https://workflows.googleapis.com/v1';

    try {
        const data = await gcpFetch(`${WORKFLOWS_API}/${parent}/workflows`);
        const wfs = data.workflows || [];

        return wfs.map((wf: any) => {
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
    } catch (err) {
        console.error('Error fetching workflows:', err);
        return [];
    }
}

export interface WorkflowExecution {
    stepName: string;
    status: string;
    executionId: string;
    revision: string;
    created: string;
    started: string;
    ended: string;
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
