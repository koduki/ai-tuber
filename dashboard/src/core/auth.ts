import { OAuth2Client } from 'google-auth-library';
import { config } from '../config';
import * as gcp from '../gcpClient';

export interface UserSession {
    tokens: any;
    userEmail: string;
}

/**
 * ユーザーがプロジェクトに対する権限を持っているかチェック
 */
export async function checkUserPermission(email: string): Promise<boolean> {
    // 1. 環境変数によるホワイトリストチェック (IAM反映遅延対策)
    const allowedEmails = (process.env.ALLOWED_EMAILS || '').split(',').map(e => e.trim());
    if (allowedEmails.includes(email)) {
        console.log(`Auth: User ${email} allowed via ALLOWED_EMAILS`);
        return true;
    }

    // 2. GCP IAM 権限によるチェック
    return await gcp.checkUserPermission(email);
}

/**
 * OAuth クライアントの取得
 */
export function getOAuth2Client() {
    return new OAuth2Client(
        config.auth.clientId,
        config.auth.clientSecret,
        config.auth.redirectUri
    );
}
