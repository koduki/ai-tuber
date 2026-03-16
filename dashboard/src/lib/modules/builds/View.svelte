<script lang="ts">
    import { onMount } from 'svelte';
    import { getStatusClass } from '$lib/utils/formatters';
    import * as Icons from 'lucide-svelte';

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
</script>

<div class="builds-container">
    <div class="flex justify-between items-center mb-6">
        <h2 class="text-lg font-medium text-gray-800">ビルド履歴 (最近の10件)</h2>
        <button class="btn-primary flex items-center gap-2 text-sm" onclick={fetchBuilds}>
            <Icons.RotateCw size={14} />
            <span>更新</span>
        </button>
    </div>
    
    {#if loading}
        <div class="animate-pulse space-y-4">
            {#each Array(5) as _}
                <div class="h-16 bg-gray-50 rounded border border-gray-100"></div>
            {/each}
        </div>
    {:else}
        <div class="card overflow-hidden">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>ビルド ID</th>
                        <th>ステータス</th>
                        <th>リポジトリ / ソース</th>
                        <th>ブランチ / コミット</th>
                    </tr>
                </thead>
                <tbody>
                    {#each builds as build}
                        <tr>
                            <td>
                                <div class="flex items-center gap-2">
                                    <Icons.Clock size={14} class="text-gray-400" />
                                    <code class="text-blue-600 font-mono text-sm font-medium">{build.id}</code>
                                </div>
                            </td>
                            <td>
                                <span class="{getStatusClass(build.status)}">
                                    {build.status}
                                </span>
                            </td>
                            <td class="text-sm text-gray-600">{build.source || 'GitHub'}</td>
                            <td>
                                <div class="text-sm font-medium text-gray-700">{build.ref || 'main'}</div>
                                <div class="flex items-center gap-1 text-[11px] text-gray-400 font-mono">
                                    <Icons.GitCommit size={12} />
                                    <span>{build.commit}</span>
                                </div>
                            </td>
                        </tr>
                    {/each}
                </tbody>
            </table>
        </div>
    {/if}
</div>
