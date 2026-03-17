import { InstancesClient } from '@google-cloud/compute';
import { config } from '../../config';

const compute = new InstancesClient();

export interface ComputeInstance {
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
