import { CloudBuildClient } from '@google-cloud/cloudbuild';
import { config } from '../../config';

const cloudBuild = new CloudBuildClient();

export interface CloudBuild {
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
