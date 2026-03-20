export const CONSOLE_BASE = 'https://console.cloud.google.com';
export const PROJECT_ID = 'ren-studio-ai'; // Or dynamic if needed

export function getConsoleUrl(type: string, item: any, projectId: string = PROJECT_ID): string {
    const base = `${CONSOLE_BASE}`;
    const p = `project=${projectId}`;
    let url = '#';
    switch (type) {
        case 'scheduler':
            url = `${base}/cloudscheduler/jobs/edit/${item.region}/${item.name}?${p}`;
            break;
        case 'workflow':
            url = `${base}/workflows/workflow/${item.location}/${item.name}/executions?${p}`;
            break;
        case 'execution':
            // 実行詳細画面は単数形の 'execution' かつ末尾に /summary が必要
            url = `${base}/workflows/workflow/${item.location || 'asia-northeast1'}/ai-tuber-streaming-pipeline/execution/${item.executionId}/summary?${p}`;
            break;
        case 'service':
            url = `${base}/run/detail/${item.region}/${item.name}/revisions?${p}`;
            break;
        case 'job':
            url = `${base}/run/jobs/details/${item.region}/${item.name}/executions?${p}`;
            break;
        case 'compute':
            url = `${base}/compute/instancesDetail/zones/${item.zone}/instances/${item.name}?${p}`;
            break;
        case 'build':
            const buildId = item.fullId || item.id;
            url = `${base}/cloud-build/builds/${buildId}?${p}`;
            if (item.region && item.region !== 'global') {
                url += `&region=${item.region}`;
            }
            break;
        case 'trigger':
            url = `${base}/cloud-build/triggers/edit/${item.triggerId || item.triggerName}?${p}`;
            break;
        default:
            url = '#';
    }
    return url;
}
