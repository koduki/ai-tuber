import { json } from '@sveltejs/kit';
import * as scheduler from '../../lib/gcp/scheduler';
import * as workflows from '../../lib/gcp/workflows';
import * as run from '../../lib/gcp/run';
import * as compute from '../../lib/gcp/compute';
import * as billing from '../../lib/gcp/billing';
import type { ModuleApi } from '../../lib/types/module';

async function getOverview() {
    const [schedulerJobs, executions, services, jobs, instances, billingSummary] = await Promise.all([
        scheduler.getSchedulerJobs().catch(() => []),
        workflows.getWorkflowExecutions().catch(() => []),
        run.getCloudRunServices().catch(() => []),
        run.getCloudRunJobs().catch(() => []),
        compute.getComputeInstances().catch(() => []),
        billing.getBillingSummary().catch(() => ({ monthlyCost: '$0.00', budget: '$0.00', detail: 'データなし', currency: 'USD' })),
    ]);

    const schedulerOk = schedulerJobs.every(j => j.lastStatus === '成功');
    const workflowOk = (executions[0]?.status === '成功');

    return {
        schedulerHealth: { value: schedulerOk ? 'OK' : 'エラー', detail: schedulerOk ? '直近実行は成功' : '失敗あり' },
        workflowState: { value: workflowOk ? '正常' : 'エラー', detail: workflowOk ? '最新 execution は成功' : '以前の実行に失敗あり' },
        runningResources: { value: services.length + jobs.length + instances.length, detail: `Run ${services.length} / Job ${jobs.length} / VM ${instances.length}` },
        externalIps: { value: instances.filter(i => i.externalIp).length, detail: '確認用 IP あり' },
        billing: { value: (billingSummary as any).monthlyCost, detail: `予算 ${(billingSummary as any).budget} / ${(billingSummary as any).currency}` },
    };
}

export const GET: ModuleApi['GET'] = {
    'stats': async () => {
        const stats = await getOverview();
        return json(stats);
    }
};
