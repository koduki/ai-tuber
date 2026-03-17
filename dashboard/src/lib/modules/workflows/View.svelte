<script lang="ts">
    import { onMount } from 'svelte';
    import { getStatusClass } from '$lib/utils/formatters';
    import { getConsoleUrl } from '$lib/utils/consoleLinks';

    let data = $state<{ workflows: any[], executions: any[] } | null>(null);
    let loading = $state(true);

    onMount(async () => {
        try {
            const res = await fetch('/api/modules/workflows/index');
            data = await res.json();
        } catch (err) {
            console.error('Workflows fetch error:', err);
        } finally {
            loading = false;
        }
    });

    function getDotClass(status: string) {
        const cls = getStatusClass(status);
        if (cls === 'status-success') return 'bg-google-green';
        if (cls === 'status-error') return 'bg-google-red';
        if (cls === 'status-warning') return 'bg-google-amber-dark';
        if (cls === 'status-blue') return 'bg-google-blue';
        return 'bg-google-gray-500';
    }

    const firstWorkflow = $derived(data?.workflows?.[0]);
    const latestExec = $derived(data?.executions?.[0]);
</script>

<div>
    {#if loading}
        <div class="text-google-gray-500 text-[13px] text-center py-6">読み込み中...</div>
    {:else if data}
        <!-- Workflow Detail Box (Top Summary) -->
        {#if firstWorkflow}
            <div class="border border-google-gray-300 rounded-lg p-4 mb-3 bg-white">
                <div class="flex justify-between items-center mb-3 text-[12px] text-google-gray-500">
                    <div>ワークフロー: <a href={getConsoleUrl('workflow', firstWorkflow)} target="_blank" rel="noopener" class="text-google-blue font-medium hover:underline">{firstWorkflow.name}</a></div>
                    {#if latestExec}
                        <div class="flex items-center gap-2">
                            現在状態: 
                            <span class="inline-flex items-center gap-1.5 font-medium {getStatusClass(latestExec.status)}">
                                <span class="w-2.5 h-2.5 rounded-full {getDotClass(latestExec.status)}"></span>
                                {latestExec.status === '成功' ? '正常' : latestExec.status}
                            </span>
                        </div>
                    {/if}
                </div>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-[12px] text-google-gray-500">
                    <div>
                        <div class="mb-1">場所</div>
                        <div class="text-[13px] text-google-gray-900">{firstWorkflow.location}</div>
                    </div>
                    <div>
                        <div class="mb-1">最新のリビジョン</div>
                        <div class="text-[13px] text-google-gray-900">{firstWorkflow.revision}</div>
                    </div>
                    <div>
                        <div class="mb-1">直近実行</div>
                        <div class="text-[13px] text-google-gray-900">{latestExec ? latestExec.created : '—'}</div>
                    </div>
                    <div>
                        <div class="mb-1">ラベル</div>
                        <div class="text-[13px] text-google-gray-900">{firstWorkflow.labels || '—'}</div>
                    </div>
                </div>
            </div>
        {/if}

        <!-- Executions Table -->
        <div class="bg-white border border-google-gray-300 rounded-lg overflow-hidden mb-6 shadow-sm">
            <div class="flex justify-between items-center px-4 py-3 border-b border-google-gray-200 bg-google-gray-50/50">
                <h2 class="text-sm font-medium text-google-gray-900 m-0">実行履歴</h2>
            </div>
            <div class="p-0 overflow-x-auto">
                <table class="w-full text-left text-[13px] text-google-gray-700 border-collapse">
                    <thead class="bg-google-gray-50">
                        <tr>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">状態</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">実行 ID</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">リビジョン</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">作成日時</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">開始時刻</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">終了時間</th>
                        </tr>
                    </thead>
                    <tbody>
                        {#each data.executions as ex}
                            <tr class="border-b border-google-gray-200 hover:bg-google-gray-50 last:border-b-0">
                                <td class="px-4 py-3 align-top whitespace-nowrap">
                                    <div class="flex items-center gap-2">
                                        <span class="w-2.5 h-2.5 rounded-full {getDotClass(ex.status)}"></span>
                                        <span class="inline-block px-2.5 py-1 rounded-full bg-google-gray-200 text-[11px] font-medium text-google-gray-500">{ex.stepName || 'exec'}</span>
                                        <span class="text-[12px] font-medium {getStatusClass(ex.status)}">{ex.status}</span>
                                    </div>
                                </td>
                                <td class="px-4 py-3 align-top whitespace-nowrap">
                                    <a href={getConsoleUrl('execution', ex)} target="_blank" rel="noopener" class="text-google-blue hover:underline">{ex.executionId}</a>
                                </td>
                                <td class="px-4 py-3 align-top whitespace-nowrap">{ex.revision}</td>
                                <td class="px-4 py-3 align-top whitespace-nowrap">{ex.created}</td>
                                <td class="px-4 py-3 align-top whitespace-nowrap">{ex.started}</td>
                                <td class="px-4 py-3 align-top whitespace-nowrap">{ex.ended}</td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
        </div>
    {/if}
</div>
