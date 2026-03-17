<script lang="ts">
    import { onMount } from 'svelte';
    import { getStatusClass } from '$lib/utils/formatters';
    import { getConsoleUrl } from '$lib/utils/consoleLinks';

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
                <h2 class="text-sm font-medium text-google-gray-900 m-0">Compute Engine インスタンス</h2>
                <button class="bg-white border-0 text-google-blue text-xs font-medium cursor-pointer hover:underline" onclick={fetchInstances}>
                    更新
                </button>
            </div>
            <div class="p-0 overflow-x-auto">
                <table class="w-full text-left text-[13px] text-google-gray-700 border-collapse">
                    <thead class="bg-google-gray-50">
                        <tr>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">状態</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">名前</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">ゾーン</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">内部 IP</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">外部 IP</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">用途</th>
                        </tr>
                    </thead>
                    <tbody>
                        {#each instances as inst}
                            <tr class="border-b border-google-gray-200 hover:bg-google-gray-50 last:border-b-0">
                                <td class="px-4 py-3 align-top whitespace-nowrap">
                                    <span class="inline-flex items-center gap-2 text-xs font-medium {getStatusClass(inst.status)}">
                                        <span class="w-2.5 h-2.5 rounded-full {getDotClass(inst.status)}"></span>
                                        {inst.status}
                                    </span>
                                </td>
                                <td class="px-4 py-3 align-top whitespace-nowrap">
                                    <a href={getConsoleUrl('compute', inst)} target="_blank" rel="noopener" class="text-google-blue font-medium hover:underline">{inst.name}</a>
                                </td>
                                <td class="px-4 py-3 align-top whitespace-nowrap">{inst.zone}</td>
                                <td class="px-4 py-3 align-top whitespace-nowrap font-bold">{inst.internalIp || 'N/A'}</td>
                                <td class="px-4 py-3 align-top whitespace-nowrap font-bold">{inst.externalIp || 'N/A'}</td>
                                <td class="px-4 py-3 align-top whitespace-nowrap">{inst.description}</td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
        </div>
    {/if}
</div>
