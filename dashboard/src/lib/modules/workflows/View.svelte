<script lang="ts">
    import { onMount } from 'svelte';
    import { getStatusClass } from '$lib/utils/formatters';

    let data = $state<{ workflows: any[], executions: any[] } | null>(null);
    let loading = $state(true);

    async function fetchData() {
        loading = true;
        try {
            const res = await fetch('/api/modules/workflows/all');
            data = await res.json();
        } catch (err) {
            console.error('Workflows fetch error:', err);
        } finally {
            loading = false;
        }
    }

    onMount(fetchData);

    function getDotClass(status: string) {
        const cls = getStatusClass(status);
        if (cls === 'status-success') return 'bg-google-green';
        if (cls === 'status-error') return 'bg-google-red';
        if (cls === 'status-warning') return 'bg-google-amber-dark';
        if (cls === 'status-blue') return 'bg-google-blue';
        return 'bg-google-gray-500';
    }
</script>

<div>
    {#if loading}
        <div class="text-google-gray-500 text-[13px] text-center py-6">読み込み中...</div>
    {:else if data}
        <!-- Workflows Table -->
        <div class="bg-white border border-google-gray-300 rounded-lg overflow-hidden mb-6">
            <div class="flex justify-between items-center px-4 py-3 border-b border-google-gray-200">
                <h2 class="text-sm font-medium text-google-gray-900 m-0">ワークフロー 詳細</h2>
                <button class="bg-white border-0 text-google-blue text-xs font-medium cursor-pointer hover:underline" onclick={fetchData}>
                    更新
                </button>
            </div>
            <div class="p-0 overflow-x-auto">
                <table class="w-full text-left text-[13px] text-google-gray-700 border-collapse">
                    <thead class="bg-google-gray-50">
                        <tr>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">名前</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">場所</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">リビジョン</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">更新日</th>
                        </tr>
                    </thead>
                    <tbody>
                        {#each data.workflows as wf}
                            <tr class="border-b border-google-gray-200 hover:bg-google-gray-50 last:border-b-0">
                                <td class="px-4 py-3 align-top whitespace-nowrap">
                                    <a href="#" class="text-google-blue font-medium hover:underline">{wf.name}</a>
                                </td>
                                <td class="px-4 py-3 align-top whitespace-nowrap">{wf.location}</td>
                                <td class="px-4 py-3 align-top whitespace-nowrap">{wf.revision}</td>
                                <td class="px-4 py-3 align-top whitespace-nowrap">{wf.updated}</td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Executions Table -->
        <div class="bg-white border border-google-gray-300 rounded-lg overflow-hidden mb-6">
            <div class="flex justify-between items-center px-4 py-3 border-b border-google-gray-200">
                <h2 class="text-sm font-medium text-google-gray-900 m-0">実行履歴</h2>
            </div>
            <div class="p-0 overflow-x-auto">
                <table class="w-full text-left text-[13px] text-google-gray-700 border-collapse">
                    <thead class="bg-google-gray-50">
                        <tr>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">状態</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">実行 ID</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">開始時刻</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">現在のステップ</th>
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
                                    <a href="#" class="text-google-blue hover:underline">{ex.executionId}</a>
                                </td>
                                <td class="px-4 py-3 align-top whitespace-nowrap">{ex.started}</td>
                                <td class="px-4 py-3 align-top whitespace-nowrap">{ex.stepName}</td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
        </div>
    {:else}
        <div class="bg-[#fce8e6] text-google-red p-3 px-4 rounded-lg text-[13px]">
            データ取得に失敗しました。
        </div>
    {/if}
</div>
