import type { ModuleMetadata } from '../../lib/types/module';

export const metadata: ModuleMetadata = {
    title: 'モジュール名',      // サイドバーに表示される名前
    icon: 'LayoutDashboard',   // Lucide-Svelte のアイコン名
    priority: 50               // 数値が小さいほど上位に表示
};
