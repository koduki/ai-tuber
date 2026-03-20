<script lang="ts">
    import { onMount } from 'svelte';
    import { getStatusClass } from '$lib/utils/formatters';
    import { getConsoleUrl } from '$lib/utils/consoleLinks';

    let builds = $state<any[]>([]);
    let loading = $state(true);

    async function fetchBuilds() {
        loading = true;
        try {
            const res = await fetch('/api/modules/builds/index');
            builds = await res.json();
        } catch (err) {
            console.error('Builds fetch error:', err);
        } finally {
            loading = false;
        }
    }

    onMount(fetchBuilds);

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
    {:else}
        <div class="bg-white border border-google-gray-300 rounded-lg overflow-hidden mb-6">
            <div class="flex justify-between items-center px-4 py-3 border-b border-google-gray-200">
                <h2 class="text-sm font-medium text-google-gray-900 m-0">Cloud Build 履歴</h2>
                <button class="bg-white border-0 text-google-blue text-xs font-medium cursor-pointer hover:underline" onclick={fetchBuilds}>
                    更新
                </button>
            </div>
            <div class="p-0 overflow-x-auto">
                <div class="flex items-center gap-2 px-3 py-2 border-b border-google-gray-300 bg-google-gray-50 text-xs text-google-gray-500">
                    <span>フィルタ</span>
                    <span class="bg-white px-2 py-0.5 rounded text-google-gray-700">プロパティ名または値を入力</span>
                </div>
                <table class="w-full text-left text-[13px] text-google-gray-700 border-collapse">
                    <thead class="bg-google-gray-50">
                        <tr>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">ステータス</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">ビルド</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">実行時間</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">所要時間</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">ソース</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">Ref</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">commit</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">トリガー名</th>
                        </tr>
                    </thead>
                    <tbody>
                        {#each builds as build}
                            <tr class="border-b border-google-gray-200 hover:bg-google-gray-50 last:border-b-0">
                                <td class="px-4 py-3 align-top whitespace-nowrap">
                                    <span class="inline-flex items-center gap-2 text-xs font-medium {getStatusClass(build.status)}">
                                        <span class="w-2.5 h-2.5 rounded-full {getDotClass(build.status)}"></span>
                                        {build.status}
                                    </span>
                                </td>
                                <td class="px-4 py-3 align-top whitespace-nowrap">
                                    <a href={getConsoleUrl('build', build)} target="_blank" rel="noopener" class="text-google-blue font-medium hover:underline">{build.id}</a>
                                </td>
                                <td class="px-4 py-3 align-top whitespace-nowrap">{build.startTime}</td>
                                <td class="px-4 py-3 align-top whitespace-nowrap">{build.duration}</td>
                                <td class="px-4 py-3 align-top whitespace-nowrap"><span class="text-google-blue hover:underline cursor-default">{build.source || 'GitHub'}</span></td>
                                <td class="px-4 py-3 align-top whitespace-nowrap">{build.ref || 'main'}</td>
                                <td class="px-4 py-3 align-top whitespace-nowrap"><span class="text-google-blue hover:underline cursor-default">{build.commit}</span></td>
                                <td class="px-4 py-3 align-top whitespace-nowrap">
                                    {#if build.triggerName}
                                        <a href={getConsoleUrl('trigger', build)} target="_blank" rel="noopener" class="text-google-blue hover:underline">{build.triggerName}</a>
                                    {:else}
                                        {''}
                                    {/if}
                                </td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
        </div>
    {/if}
</div>
