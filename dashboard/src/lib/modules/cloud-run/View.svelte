<script lang="ts">
    import { onMount } from 'svelte';
    import { getStatusClass } from '$lib/utils/formatters';
    import { getConsoleUrl, PROJECT_ID } from '$lib/utils/consoleLinks';

    let services = $state<any[]>([]);
    let jobs = $state<any[]>([]);
    let loading = $state(true);

    async function fetchData() {
        loading = true;
        try {
            const [resSvc, resJob] = await Promise.all([
                fetch('/api/modules/cloud-run/services'),
                fetch('/api/modules/cloud-run/jobs')
            ]);
            services = await resSvc.json();
            jobs = await resJob.json();
        } catch (err) {
            console.error('Cloud Run fetch error:', err);
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
    {:else}
        <!-- Cloud Run Services -->
        <div class="bg-white border border-google-gray-300 rounded-lg overflow-hidden mb-6">
            <div class="flex justify-between items-center px-4 py-3 border-b border-google-gray-200">
                <h2 class="text-sm font-medium text-google-gray-900 m-0">Cloud Run サービス</h2>
                <button class="bg-white border-0 text-google-blue text-xs font-medium cursor-pointer hover:underline" onclick={fetchData}>
                    更新
                </button>
            </div>
            <div class="p-0 overflow-x-auto">
                <table class="w-full text-left text-[13px] text-google-gray-700 border-collapse">
                    <thead class="bg-google-gray-50">
                        <tr>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">状態</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">名前</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">リージョン</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">認証</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">Ingress</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">URI</th>
                        </tr>
                    </thead>
                    <tbody>
                        {#each services as svc}
                            <tr class="border-b border-google-gray-200 hover:bg-google-gray-50 last:border-b-0">
                                <td class="px-4 py-3 align-top whitespace-nowrap">
                                    <span class="inline-flex items-center gap-2 text-xs font-medium {getStatusClass(svc.status)}">
                                        <span class="w-2.5 h-2.5 rounded-full {getDotClass(svc.status)}"></span>
                                        {svc.status}
                                    </span>
                                </td>
                                <td class="px-4 py-3 align-top whitespace-nowrap">
                                    <a href={getConsoleUrl('service', svc)} target="_blank" rel="noopener" class="text-google-blue font-medium hover:underline">{svc.name}</a>
                                </td>
                                <td class="px-4 py-3 align-top whitespace-nowrap">{svc.region}</td>
                                <td class="px-4 py-3 align-top whitespace-nowrap">{svc.authentication}</td>
                                <td class="px-4 py-3 align-top whitespace-nowrap">{svc.ingress}</td>
                                <td class="px-4 py-3 align-top whitespace-nowrap">
                                    <a href={svc.uri} target="_blank" rel="noopener" class="text-google-blue hover:underline">{svc.uri}</a>
                                </td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Cloud Run Jobs -->
        <div class="bg-white border border-google-gray-300 rounded-lg overflow-hidden mb-6">
            <div class="flex justify-between items-center px-4 py-3 border-b border-google-gray-200">
                <h2 class="text-sm font-medium text-google-gray-900 m-0">Cloud Run ジョブ</h2>
            </div>
            <div class="p-0 overflow-x-auto">
                <table class="w-full text-left text-[13px] text-google-gray-700 border-collapse">
                    <thead class="bg-google-gray-50">
                        <tr>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">状態</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">名前</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">最終実行</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">リージョン</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">トリガー</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">作成者</th>
                        </tr>
                    </thead>
                    <tbody>
                        {#each jobs as job}
                            <tr class="border-b border-google-gray-200 hover:bg-google-gray-50 last:border-b-0">
                                <td class="px-4 py-3 align-top whitespace-nowrap">
                                    <span class="inline-flex items-center gap-2 text-xs font-medium {getStatusClass(job.status)}">
                                        <span class="w-2.5 h-2.5 rounded-full {getDotClass(job.status)}"></span>
                                        {job.status}
                                    </span>
                                </td>
                                <td class="px-4 py-3 align-top whitespace-nowrap">
                                    <a href={getConsoleUrl('job', job)} target="_blank" rel="noopener" class="text-google-blue font-medium hover:underline">{job.name}</a>
                                </td>
                                <td class="px-4 py-3 align-top whitespace-nowrap">{job.lastExecution}</td>
                                <td class="px-4 py-3 align-top whitespace-nowrap">{job.region}</td>
                                <td class="px-4 py-3 align-top whitespace-nowrap">{job.trigger}</td>
                                <td class="px-4 py-3 align-top whitespace-nowrap truncate max-w-[150px]" title={job.creator}>{job.creator}</td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
        </div>
    {/if}
</div>
