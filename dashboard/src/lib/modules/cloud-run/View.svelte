<script lang="ts">
    import { onMount } from 'svelte';
    import { getStatusClass } from '$lib/utils/formatters';
    import * as Icons from 'lucide-svelte';

    let services = $state<any[]>([]);
    let loading = $state(true);

    async function fetchServices() {
        loading = true;
        try {
            const res = await fetch('/api/modules/cloud-run/services');
            services = await res.json();
        } catch (err) {
            console.error('Cloud Run fetch error:', err);
        } finally {
            loading = false;
        }
    }

    onMount(fetchServices);
</script>

<div class="cloud-run-container">
    <div class="flex justify-between items-center mb-6">
        <h2 class="text-lg font-medium text-gray-800">サービス一覧 (Run v2)</h2>
        <button class="btn-primary flex items-center gap-2 text-sm" onclick={fetchServices}>
            <Icons.RotateCw size={14} />
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
                        <th>サービス名</th>
                        <th>ステータス</th>
                        <th>リージョン</th>
                        <th>認証</th>
                        <th>URL</th>
                    </tr>
                </thead>
                <tbody>
                    {#each services as svc}
                        <tr>
                            <td class="font-medium text-gray-900">{svc.name}</td>
                            <td>
                                <span class="{getStatusClass(svc.status)}">
                                    {svc.status}
                                </span>
                            </td>
                            <td class="text-sm text-gray-600">{svc.region}</td>
                            <td class="text-xs text-gray-500">{svc.authentication}</td>
                            <td>
                                <a href={svc.uri} target="_blank" rel="noreferrer" class="text-blue-600 hover:text-blue-800 flex items-center gap-1">
                                    <Icons.ExternalLink size={14} />
                                    <span>開く</span>
                                </a>
                            </td>
                        </tr>
                    {/each}
                </tbody>
            </table>
        </div>
    {/if}
</div>
