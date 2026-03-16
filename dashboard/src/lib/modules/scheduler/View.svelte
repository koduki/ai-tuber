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
</script>

<div class="scheduler-container">
    <div class="flex justify-between items-center mb-6">
        <h2 class="text-lg font-medium text-gray-800">ジョブ一覧</h2>
        <button class="btn-primary flex items-center gap-2 text-sm" onclick={fetchJobs}>
            <RotateCw size={14} />
            <span>更新</span>
        </button>
    </div>
    
    {#if loading}
        <div class="animate-pulse space-y-4">
            {#each Array(3) as _}
                <div class="h-16 bg-gray-50 rounded border border-gray-100"></div>
            {/each}
        </div>
    {:else}
        <div class="card overflow-hidden">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>名前</th>
                        <th>頻度 (Cron)</th>
                        <th>最後の実行</th>
                        <th>次回の実行</th>
                        <th>ステータス</th>
                        <th class="text-right">アクション</th>
                    </tr>
                </thead>
                <tbody>
                    {#each jobs as job}
                        <tr>
                            <td>
                                <div class="font-medium text-gray-900">{job.displayName}</div>
                                <div class="text-xs text-gray-500 mt-0.5">{job.description || 'Cloud Scheduler Job'}</div>
                            </td>
                            <td><code class="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded font-mono">{job.schedule}</code></td>
                            <td class="text-sm text-gray-600 font-mono">{job.lastRunTime}</td>
                            <td class="text-sm text-gray-600 font-mono">{job.nextRunTime}</td>
                            <td>
                                <span class="{getStatusClass(job.lastStatus)}">
                                    {job.lastStatus}
                                </span>
                            </td>
                            <td class="text-right">
                                <button class="p-2 hover:bg-blue-50 text-blue-600 rounded transition-colors" onclick={() => runJob(job.name)} title="実行">
                                    <Play size={16} fill="currentColor" />
                                </button>
                            </td>
                        </tr>
                    {/each}
                </tbody>
            </table>
        </div>
    {/if}
</div>
