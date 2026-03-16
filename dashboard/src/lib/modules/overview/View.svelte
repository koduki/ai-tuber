<script lang="ts">
    import { onMount } from 'svelte';
    import { formatCurrency, getStatusClass } from '$lib/utils/formatters';
    import * as Icons from 'lucide-svelte';

    let data = $state<any>(null);
    let loading = $state(true);

    onMount(async () => {
        try {
            const res = await fetch('/api/modules/overview/index');
            data = await res.json();
        } catch (err) {
            console.error('Overview fetch error:', err);
        } finally {
            loading = false;
        }
    });

    const metrics = $derived(data ? [
        { 
            label: 'Cloud Scheduler', 
            id: 'mc-scheduler',
            value: data.schedulerHealth.value, 
            sub: data.schedulerHealth.detail,
            icon: Icons.Calendar,
            status: getStatusClass(data.schedulerHealth.value)
        },
        { 
            label: 'Cloud Workflows', 
            id: 'mc-workflow',
            value: data.workflowState.value, 
            sub: data.workflowState.detail,
            icon: Icons.Network,
            status: getStatusClass(data.workflowState.value)
        },
        { 
            label: '稼働リソース', 
            id: 'mc-resources',
            value: data.runningResources.value, 
            sub: data.runningResources.detail,
            icon: Icons.Server,
            status: 'status-neutral'
        },
        { 
            label: '外部 IP (Compute)', 
            id: 'mc-ips',
            value: data.externalIps.value, 
            sub: data.externalIps.detail,
            icon: Icons.Globe,
            status: 'status-neutral'
        },
        { 
            label: '今月のコスト', 
            id: 'mc-billing',
            value: data.billing.value, 
            sub: data.billing.detail,
            icon: Icons.CreditCard,
            status: 'status-neutral'
        },
    ] : []);

    const quickLinks = [
        { title: 'Cloud Run Services', desc: '本番サービス一覧', icon: Icons.Cloud, url: '#' },
        { title: 'Cloud Build', desc: '履歴とログ', icon: Icons.Hammer, url: '#' },
        { title: 'API Monitoring', desc: 'Google API Console', icon: Icons.Activity, url: '#' },
    ];
</script>

<div class="overview-container">
    <div class="metrics">
        {#if loading}
            {#each Array(5) as _}
                <div class="metric-card animate-pulse h-32 bg-gray-50 border-gray-100"></div>
            {/each}
        {:else}
            {#each metrics as metric}
                <div class="metric-card" id={metric.id}>
                    <div class="flex justify-between items-start mb-2">
                        <span class="metric-card__label">{metric.label}</span>
                        <metric.icon size={16} class="text-gray-400" />
                    </div>
                    <div class="metric-card__value {metric.status}">
                        {metric.value}
                    </div>
                    <div class="metric-card__footer">
                        <span class="metric-card__sub">{metric.sub}</span>
                    </div>
                </div>
            {/each}
        {/if}
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="card">
            <div class="card-header">
                <span>クイックリンク</span>
                <Icons.ExternalLink size={14} class="text-gray-400" />
            </div>
            <div class="card-body p-0">
                <div class="divide-y divide-gray-100">
                    {#each quickLinks as link}
                        <a href={link.url} class="flex items-center gap-4 p-4 hover:bg-gray-50 transition-colors">
                            <div class="w-10 h-10 rounded bg-blue-50 flex items-center justify-center text-blue-600">
                                <link.icon size={18} />
                            </div>
                            <div>
                                <div class="text-sm font-medium text-gray-900">{link.title}</div>
                                <div class="text-xs text-gray-500">{link.desc}</div>
                            </div>
                        </a>
                    {/each}
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-header">
                <span>システムステータス</span>
                <Icons.Info size={14} class="text-gray-400" />
            </div>
            <div class="card-body">
                <div class="space-y-4">
                    <div class="flex items-center justify-between">
                        <span class="text-sm text-gray-600">プラットフォーム可用性</span>
                        <span class="text-sm font-medium text-green-600">100.0%</span>
                    </div>
                    <div class="w-full bg-gray-100 rounded-full h-1.5">
                        <div class="bg-green-500 h-1.5 rounded-full" style="width: 100%"></div>
                    </div>
                    <div class="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-100">
                        <div class="flex gap-3">
                            <Icons.AlertCircle size={18} class="text-blue-600 flex-shrink-0" />
                            <div class="text-xs text-blue-800 leading-relaxed">
                                全てのシステムは正常に稼働しています。監視対象のリージョン（us-central1, asia-northeast1）で異常は検出されていません。
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
