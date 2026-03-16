<script lang="ts">
    import { onMount } from 'svelte';
    import { getStatusClass } from '$lib/utils/formatters';
    import * as Icons from 'lucide-svelte';

    let instances = $state<any[]>([]);
    let loading = $state(true);

    async function fetchInstances() {
        loading = true;
        try {
            const res = await fetch('/api/modules/compute/index');
            instances = await res.json();
        } catch (err) {
            console.error('Compute fetch error:', err);
        } finally {
            loading = false;
        }
    }

    onMount(fetchInstances);
</script>

<div class="compute-container">
    <div class="flex justify-between items-center mb-6">
        <h2 class="text-lg font-medium text-gray-800">インスタンス一覧</h2>
        <button class="btn-primary flex items-center gap-2 text-sm" onclick={fetchInstances}>
            <Icons.RotateCw size={14} />
            <span>更新</span>
        </button>
    </div>
    
    {#if loading}
        <div class="animate-pulse space-y-4">
            {#each Array(2) as _}
                <div class="h-20 bg-gray-50 rounded border border-gray-100"></div>
            {/each}
        </div>
    {:else}
        <div class="card overflow-hidden">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>インスタンス名</th>
                        <th>ステータス</th>
                        <th>ゾーン</th>
                        <th>IP アドレス</th>
                    </tr>
                </thead>
                <tbody>
                    {#each instances as inst}
                        <tr>
                            <td>
                                <div class="font-medium text-gray-900">{inst.name}</div>
                                <div class="text-xs text-gray-400 mt-0.5">{inst.description}</div>
                            </td>
                            <td>
                                <span class="{getStatusClass(inst.status)}">
                                    {inst.status}
                                </span>
                            </td>
                            <td class="text-sm text-gray-600 font-mono">{inst.zone}</td>
                            <td>
                                <div class="flex flex-col gap-1">
                                    <div class="flex items-center gap-2">
                                        <span class="text-[10px] font-bold text-gray-400 w-8 uppercase">Ext:</span>
                                        <span class="text-xs font-mono text-gray-700">{inst.externalIp || 'N/A'}</span>
                                    </div>
                                    <div class="flex items-center gap-2">
                                        <span class="text-[10px] font-bold text-gray-400 w-8 uppercase">Int:</span>
                                        <span class="text-xs font-mono text-gray-500">{inst.internalIp || 'N/A'}</span>
                                    </div>
                                </div>
                            </td>
                        </tr>
                    {/each}
                </tbody>
            </table>
        </div>
    {/if}
</div>
