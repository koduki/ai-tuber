/**
 * プレゼンテーション用フォーマッタ
 */

/** 通貨フォーマット (JPY/USD対応) */
export function formatCurrency(value: number | string, currency = 'USD'): string {
    const num = typeof value === 'string' ? parseFloat(value.replace(/[^0-9.-]+/g, "")) : value;
    if (isNaN(num)) return String(value);

    return new Intl.NumberFormat('ja-JP', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: currency === 'JPY' ? 0 : 2
    }).format(num);
}

/** 日付フォーマット (YYYY/MM/DD HH:mm) */
export function formatDate(date: Date | string | number): string {
    const d = new Date(date);
    if (isNaN(d.getTime())) return String(date);
    return d.toLocaleString('ja-JP', {
        timeZone: 'Asia/Tokyo',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    }).replace(/\//g, '/');
}

/** ステータスに応じた CSS クラス名の取得 */
export function getStatusClass(status: string): string {
    const s = status.toLowerCase();
    if (s.includes('成功') || s.includes('正常') || s.includes('稼働中') || s.includes('有効') || s.includes('完了') || s === 'ok') {
        return 'status-success';
    }
    if (s.includes('失敗') || s.includes('エラー')) {
        return 'status-error';
    }
    if (s.includes('実行中') || s.includes('起動中') || s.includes('ビルド中')) {
        return 'status-blue';
    }
    return 'status-neutral';
}

/** トレンドに応じたアイコンの取得 */
export function getTrendIcon(trend: 'up' | 'down' | 'stable'): string {
    switch (trend) {
        case 'up': return '↑';
        case 'down': return '↓';
        default: return '→';
    }
}
