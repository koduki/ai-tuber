<script lang="ts">
    import { onMount } from 'svelte';
    import { getStatusClass } from '$lib/utils/formatters';
    import SchedulerView from '../scheduler/View.svelte';
    import WorkflowsView from '../workflows/View.svelte';
    import CloudRunView from '../cloud-run/View.svelte';
    import ComputeView from '../compute/View.svelte';
    import BuildsView from '../builds/View.svelte';

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
            trend: 'stable'
        },
        { 
            label: 'Workflow 現在状態', 
            id: 'mc-workflow',
            value: data ? data.workflowState.value : '—', 
            sub: data ? data.workflowState.detail : '読み込み中...',
            status: data ? getStatusClass(data.workflowState.value) : 'status-neutral',
            trend: 'stable'
        },
        { 
            label: '稼働リソース', 
            id: 'mc-resources',
            value: data ? data.runningResources.value : '—', 
            sub: data ? data.runningResources.detail : '読み込み中...',
            status: 'status-neutral',
            trend: 'stable'
        },
        { 
            label: 'Compute 外部 IP', 
            id: 'mc-ips',
            value: data ? data.externalIps.value : '—', 
            sub: data ? data.externalIps.detail : '読み込み中...',
            status: 'status-neutral',
            trend: 'stable'
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
                    {:else if metric.trend === 'stable'}
                        <span class="text-xs font-medium text-google-gray-500">→</span>
                    {:else}
                        <span class="text-xs font-medium text-google-gray-500">—</span>
                    {/if}
                </div>
            </div>
        {/each}
    </div>

    <!-- Combined Module Views for Overview -->
    <div class="flex flex-col gap-6">
        <!-- Quick Links -->
        <div class="border border-google-gray-300 rounded-lg bg-white overflow-hidden shadow-sm">
            <div class="px-4 py-3 border-b border-google-gray-200 bg-google-gray-50/50">
                <h2 class="text-sm font-medium text-google-gray-900 m-0">クイックリンク</h2>
            </div>
            <div class="p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                <a href="https://console.cloud.google.com/run?project=ren-studio-ai" target="_blank" rel="noopener" class="p-4 border border-google-gray-300 rounded-lg hover:border-google-blue hover:bg-[#f8fbff] transition-all no-underline group">
                    <div class="text-sm font-medium text-google-gray-900 mb-1 group-hover:text-google-blue">Cloud Run Services</div>
                    <div class="text-[12px] text-google-gray-500">本番サービス一覧を開く</div>
                </a>
                <a href="https://console.cloud.google.com/run/jobs?project=ren-studio-ai" target="_blank" rel="noopener" class="p-4 border border-google-gray-300 rounded-lg hover:border-google-blue hover:bg-[#f8fbff] transition-all no-underline group">
                    <div class="text-sm font-medium text-google-gray-900 mb-1 group-hover:text-google-blue">Cloud Run Jobs</div>
                    <div class="text-[12px] text-google-gray-500">Job 実行履歴を開く</div>
                </a>
                <a href="https://console.cloud.google.com/workflows?project=ren-studio-ai" target="_blank" rel="noopener" class="p-4 border border-google-gray-300 rounded-lg hover:border-google-blue hover:bg-[#f8fbff] transition-all no-underline group">
                    <div class="text-sm font-medium text-google-gray-900 mb-1 group-hover:text-google-blue">Cloud Workflows</div>
                    <div class="text-[12px] text-google-gray-500">Executions 画面へ</div>
                </a>
                <a href="https://console.cloud.google.com/cloud-build/builds?project=ren-studio-ai" target="_blank" rel="noopener" class="p-4 border border-google-gray-300 rounded-lg hover:border-google-blue hover:bg-[#f8fbff] transition-all no-underline group">
                    <div class="text-sm font-medium text-google-gray-900 mb-1 group-hover:text-google-blue">Cloud Build</div>
                    <div class="text-[12px] text-google-gray-500">Build History へ</div>
                </a>
                <a href="https://console.cloud.google.com/logs?project=ren-studio-ai" target="_blank" rel="noopener" class="p-4 border border-google-gray-300 rounded-lg hover:border-google-blue hover:bg-[#f8fbff] transition-all no-underline group">
                    <div class="text-sm font-medium text-google-gray-900 mb-1 group-hover:text-google-blue">Logs Explorer</div>
                    <div class="text-[12px] text-google-gray-500">障害調査の入口</div>
                </a>
                <a href="https://console.cloud.google.com/monitoring?project=ren-studio-ai" target="_blank" rel="noopener" class="p-4 border border-google-gray-300 rounded-lg hover:border-google-blue hover:bg-[#f8fbff] transition-all no-underline group">
                    <div class="text-sm font-medium text-google-gray-900 mb-1 group-hover:text-google-blue">Monitoring</div>
                    <div class="text-[12px] text-google-gray-500">アラートと指標</div>
                </a>
            </div>
        </div>

        <SchedulerView />
        <WorkflowsView />
        <CloudRunView />
        <ComputeView />
        <BuildsView />
    </div>
</div>
