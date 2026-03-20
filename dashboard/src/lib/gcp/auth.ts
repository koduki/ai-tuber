import { config } from '../../config';

/**
 * GCP REST API を呼び出すためのヘルパー
 */
export async function gcpFetch(url: string): Promise<any> {
    const { GoogleAuth } = await import('google-auth-library');
    const auth = new GoogleAuth({ scopes: ['https://www.googleapis.com/auth/cloud-platform'] });
    const client = await auth.getClient();
    const token = (await client.getAccessToken()).token;
    const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
    if (!res.ok) throw new Error(`Fetch ${url} failed: ${res.status}`);
    return res.json();
}

/**
 * タイムスタンプのフォーマット
 */
export function formatTimestamp(ts?: any): string {
    if (!ts) return '';
    try {
        const d = (typeof ts === 'string') ? new Date(ts) : new Date(Number(ts.seconds || 0) * 1000);
        return d.toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' }).replace(/\//g, '/');
    } catch {
        return String(ts);
    }
}

/**
 * プロジェクトの閲覧権限チェック
 */
export async function checkUserPermission(email: string): Promise<boolean> {
    try {
        const { GoogleAuth } = await import('google-auth-library');
        const auth = new GoogleAuth({
            scopes: ['https://www.googleapis.com/auth/cloud-platform']
        });
        const client = await auth.getClient();
        const projectId = config.projectId;
        const url = `https://cloudresourcemanager.googleapis.com/v1/projects/${projectId}:getIamPolicy`;

        const res = await client.request<{ bindings: { role: string, members: string[] }[] }>({ url, method: 'POST' });
        const policy = res.data;

        const allowedRoles = [
            'roles/viewer',
            'roles/editor',
            'roles/owner',
            'roles/browser',
        ];

        const userEntries = [
            `user:${email}`,
            `domain:${email.split('@')[1]}`,
        ];

        return (policy.bindings || []).some(binding => 
            allowedRoles.includes(binding.role) && 
            binding.members.some(member => userEntries.includes(member))
        );
    } catch (err: any) {
        console.error('Permission check error:', err.message || err);
        return false;
    }
}
