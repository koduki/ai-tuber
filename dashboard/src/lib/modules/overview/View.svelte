<script lang="ts">
    import { onMount } from 'svelte';
    import { formatCurrency, getStatusClass } from '$lib/utils/formatters';

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

    const metrics = $derived([
        { 
            label: 'Scheduler 健全性', 
            id: 'mc-scheduler',
            value: data ? data.schedulerHealth.value : '—', 
            sub: data ? data.schedulerHealth.detail : '読み込み中...',
            status: data ? getStatusClass(data.schedulerHealth.value) : 'status-neutral',
            trend: 'down'
        },
        { 
            label: 'Workflow 現在状態', 
            id: 'mc-workflow',
            value: data ? data.workflowState.value : '—', 
            sub: data ? data.workflowState.detail : '読み込み中...',
            status: data ? getStatusClass(data.workflowState.value) : 'status-neutral',
            trend: 'down'
        },
        { 
            label: '稼働リソース', 
            id: 'mc-resources',
            value: data ? data.runningResources.value : '—', 
            sub: data ? data.runningResources.detail : '読み込み中...',
            status: 'status-neutral',
            trend: 'down'
        },
        { 
            label: 'Compute 外部 IP', 
            id: 'mc-ips',
            value: data ? data.externalIps.value : '—', 
            sub: data ? data.externalIps.detail : '読み込み中...',
            status: 'status-neutral',
            trend: 'down'
        },
        { 
            label: '概算コスト', 
            id: 'mc-cost',
            value: data ? data.billing.value : '—', 
            sub: data ? data.billing.detail : 'Billing API 未接続',
            status: 'status-neutral',
            trend: null
        },
    ]);
</script>

<div>
    <div class="grid gap-4 mb-6 grid-cols-2 lg:grid-cols-5">
        {#each metrics as metric}
            <div class="p-3 px-4 border border-google-gray-300 rounded-lg bg-white hover:shadow-sm transition-shadow" id={metric.id}>
                <div class="text-xs text-google-gray-500">{metric.label}</div>
                <div class="mt-2 text-[28px] font-normal tracking-tight leading-none {metric.status}">
                    {metric.value}
                </div>
                <div class="mt-2 flex justify-between items-center">
                    <span class="text-xs text-google-gray-500">{metric.sub}</span>
                    {#if metric.trend === 'down'}
                        <span class="text-xs font-medium text-google-green">↓</span>
                    {:else if metric.trend === 'up'}
                        <span class="text-xs font-medium text-google-amber-dark">↑</span>
                    {:else}
                        <span class="text-xs font-medium text-google-gray-500">—</span>
                    {/if}
                </div>
            </div>
        {/each}
    </div>

    <!-- Overview Cards -->
    <div class="flex flex-col gap-6">
        <!-- Scheduler -->
        <div class="border border-google-gray-300 rounded-lg bg-white overflow-hidden">
            <div class="flex justify-between items-center px-4 py-3 border-b border-google-gray-200">
                <h2 class="text-sm font-medium text-google-gray-900 m-0">Cloud Scheduler</h2>
            </div>
            <div class="p-4 text-[13px] text-google-gray-500">
                各モジュールのタブから詳細を確認してください。
            </div>
        </div>

        <!-- Workflows -->
        <div class="border border-google-gray-300 rounded-lg bg-white overflow-hidden">
            <div class="flex justify-between items-center px-4 py-3 border-b border-google-gray-200">
                <h2 class="text-sm font-medium text-google-gray-900 m-0">ワークフロー</h2>
            </div>
            <div class="p-4 text-[13px] text-google-gray-500">
                各モジュールのタブから詳細を確認してください。
            </div>
        </div>

        <!-- Resources -->
        <div class="border border-google-gray-300 rounded-lg bg-white overflow-hidden">
            <div class="flex justify-between items-center px-4 py-3 border-b border-google-gray-200">
                <h2 class="text-sm font-medium text-google-gray-900 m-0">稼働リソース</h2>
            </div>
            <div class="p-4 text-[13px] text-google-gray-500">
                各モジュールのタブから詳細を確認してください。
            </div>
        </div>
    </div>
</div>
