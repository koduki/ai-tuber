<script lang="ts">
    import { onMount } from 'svelte';
    import { Play, RotateCw } from 'lucide-svelte';
    import { getStatusClass } from '$lib/utils/formatters';

    let jobs = $state<any[]>([]);
    let loading = $state(true);

    async function fetchJobs() {
        loading = true;
        try {
            const res = await fetch('/api/modules/scheduler/index');
            jobs = await res.json();
        } catch (err) {
            console.error('Scheduler fetch error:', err);
        } finally {
            loading = false;
        }
    }

    onMount(fetchJobs);

    async function runJob(name: string) {
        if (!confirm(`ジョブ "${name}" を今すぐ実行しますか？`)) return;
        
        try {
            const res = await fetch(`/api/modules/scheduler/run?jobName=${name}`, { 
                method: 'POST' 
            });
            if (res.ok) {
                alert(`ジョブ "${name}" の実行をリクエストしました。`);
                fetchJobs();
            } else {
                const err = await res.json();
                alert(`実行に失敗しました: ${err.error}`);
            }
        } catch (err) {
            alert(`エラー: ${err}`);
        }
    }
    
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
    <div class="bg-white border border-google-gray-300 rounded-lg overflow-hidden mb-6">
        <div class="flex justify-between items-center px-4 py-3 border-b border-google-gray-200">
            <h2 class="text-sm font-medium text-google-gray-900 m-0">Cloud Scheduler ジョブ</h2>
            <button class="bg-white border-0 text-google-blue text-xs font-medium cursor-pointer hover:underline" onclick={fetchJobs}>
                更新
            </button>
        </div>
        <div class="p-0 overflow-x-auto">
            {#if loading}
                <div class="text-google-gray-500 text-[13px] text-center py-6">読み込み中...</div>
            {:else if jobs.length === 0}
                <div class="text-google-gray-500 text-[13px] text-center py-6">ジョブなし</div>
            {:else}
                <table class="w-full text-left text-[13px] text-google-gray-700 border-collapse">
                    <thead class="bg-google-gray-50">
                        <tr>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">名前</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">頻度</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">最後の実行</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">次回の実行</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">ステータス</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">アクション</th>
                        </tr>
                    </thead>
                    <tbody>
                        {#each jobs as job}
                            <tr class="border-b border-google-gray-200 hover:bg-google-gray-50 last:border-b-0">
                                <td class="px-4 py-3 align-top whitespace-nowrap">
                                    <div class="text-google-blue"><a href="#" class="font-medium hover:underline text-google-blue">{job.displayName}</a></div>
                                    <div class="text-[11px] text-google-gray-500 mt-1">{job.description || 'Cloud Scheduler Job'}</div>
                                </td>
                                <td class="px-4 py-3 align-top whitespace-nowrap">{job.schedule}</td>
                                <td class="px-4 py-3 align-top whitespace-nowrap">{job.lastRunTime}</td>
                                <td class="px-4 py-3 align-top whitespace-nowrap">{job.nextRunTime}</td>
                                <td class="px-4 py-3 align-top whitespace-nowrap">
                                    <span class="inline-flex items-center gap-2 text-xs font-medium {getStatusClass(job.lastStatus)}">
                                        <span class="w-2.5 h-2.5 rounded-full {getDotClass(job.lastStatus)}"></span>
                                        {job.lastStatus}
                                    </span>
                                </td>
                                <td class="px-4 py-3 align-top whitespace-nowrap">
                                    <button class="bg-google-blue text-white border-0 px-3 py-1 rounded-full text-[11px] font-medium cursor-pointer hover:bg-google-blue-hover" onclick={() => runJob(job.name)}>今すぐ実行</button>
                                </td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            {/if}
        </div>
    </div>
</div>
