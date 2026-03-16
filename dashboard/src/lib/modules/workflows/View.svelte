<script lang="ts">
    import { onMount } from 'svelte';
    import { getStatusClass } from '$lib/utils/formatters';
    import * as Icons from 'lucide-svelte';

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
</script>

<div class="workflows-container">
    {#if loading}
        <div class="space-y-8 animate-pulse">
            {#each Array(2) as _}
                <div class="h-32 bg-gray-50 rounded border border-gray-100"></div>
            {/each}
        </div>
    {:else if data}
        <section class="mb-8">
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-lg font-medium text-gray-800">ワークフロー定義</h2>
                <button class="btn-primary flex items-center gap-2 text-sm" onclick={fetchData}>
                    <Icons.RotateCw size={14} />
                    <span>更新</span>
                </button>
            </div>
            <div class="card overflow-hidden">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>ワークフロー名</th>
                            <th>ロケーション</th>
                            <th>リビジョン</th>
                            <th>最終更新</th>
                        </tr>
                    </thead>
                    <tbody>
                        {#each data.workflows as wf}
                            <tr>
                                <td class="font-medium text-gray-900">{wf.name}</td>
                                <td>{wf.location}</td>
                                <td class="text-xs font-mono text-gray-500">{wf.revision}</td>
                                <td class="text-sm text-gray-600">{wf.updated}</td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
        </section>

        <section>
            <h2 class="text-lg font-medium text-gray-800 mb-4">直近の実行履歴</h2>
            <div class="card overflow-hidden">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>実行 ID</th>
                            <th>ステータス</th>
                            <th>現在のステップ</th>
                            <th>開始時刻</th>
                        </tr>
                    </thead>
                    <tbody>
                        {#each data.executions as ex}
                            <tr>
                                <td class="text-xs text-blue-600 font-mono font-medium">{ex.executionId}</td>
                                <td>
                                    <span class="{getStatusClass(ex.status)}">
                                        {ex.status}
                                    </span>
                                </td>
                                <td class="text-sm text-gray-600">{ex.stepName}</td>
                                <td class="text-sm text-gray-500 font-mono">{ex.started}</td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
        </section>
    {:else}
        <div class="error-message">
            ワークフロー情報の取得に失敗しました。
        </div>
    {/if}
</div>
