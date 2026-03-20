/**
 * モジュールのメタデータ定義
 */
export interface ModuleMetadata {
    title: string;
    icon: string;
    priority?: number;
    description?: string;
}

/**
 * モジュール内の api.ts が実装すべきインターフェース
 * SvelteKit のエンドポイント形式をラップしたもの
 */
export interface ModuleApi {
    GET?: Record<string, (url?: URL) => Promise<Response>>;
    POST?: Record<string, (url?: URL) => Promise<Response>>;
}

/**
 * マニフェスト API が返すモジュール情報の型
 */
export interface ModuleManifest extends ModuleMetadata {
    id: string;
}
