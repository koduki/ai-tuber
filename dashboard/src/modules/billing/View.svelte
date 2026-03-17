<script lang="ts">
    import { onMount } from 'svelte';
    import { formatCurrency, formatDate, getTrendIcon } from '$lib/utils/formatters';

    let data = $state<any>(null);
    let loading = $state(true);

    onMount(async () => {
        try {
            const res = await fetch('/api/modules/billing/summary');
            data = await res.json();
        } catch (err) {
            console.error('Billing fetch error:', err);
        } finally {
            loading = false;
        }
    });

    const maxDailyCost = $derived(data?.dailyCosts?.length ? Math.max(...data.dailyCosts.map((d: any) => d.cost), 1) : 1);
</script>

<div>
    {#if loading}
        <div class="text-google-gray-500 text-[13px] text-center py-6">読み込み中...</div>
    {:else if data}
        <div class="grid gap-4 mb-6 grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
            <div class="p-3 px-4 border border-google-gray-300 rounded-lg bg-white hover:shadow-sm transition-shadow">
                <div class="text-[12px] text-google-gray-500">今月の合計</div>
                <div class="mt-2 text-[28px] font-normal tracking-tight leading-none text-google-gray-900">{data.monthlyCost || '$0.00'}</div>
            </div>
            <div class="p-3 px-4 border border-google-gray-300 rounded-lg bg-white hover:shadow-sm transition-shadow">
                <div class="text-[12px] text-google-gray-500">予算設定</div>
                <div class="mt-2 text-[28px] font-normal tracking-tight leading-none text-google-gray-900">{data.budget || '$0.00'}</div>
            </div>
            <div class="p-3 px-4 border border-google-gray-300 rounded-lg bg-white hover:shadow-sm transition-shadow">
                <div class="text-[12px] text-google-gray-500">予測 (データ収束中)</div>
                <div class="mt-2 text-[28px] font-normal tracking-tight leading-none text-google-gray-900">{data.forecast || '$0.00'}</div>
            </div>
        </div>

        <div class="bg-white border border-google-gray-300 rounded-lg overflow-hidden mb-6">
            <div class="flex justify-between items-center px-4 py-3 border-b border-google-gray-200">
                <h2 class="text-sm font-medium text-google-gray-900 m-0">日次コスト推移 (直近30日)</h2>
            </div>
            <div class="p-4">
                <div class="flex items-end gap-1 h-[200px] pt-5 pb-10 border-b border-google-gray-300 overflow-x-auto relative">
                    {#each data.dailyCosts as day}
                        <div class="flex-1 min-w-[25px] flex flex-col-reverse items-center relative h-full group cursor-pointer">
                            <div class="w-full bg-[#c2e7ff] rounded-t-[4px] min-h-[2px] transition-all group-hover:bg-[#7fcfff]" style="height: {(day.cost / maxDailyCost) * 100}%"></div>
                            <div class="opacity-0 group-hover:opacity-100 absolute -top-[30px] bg-[#3c4043] text-white px-2 py-1 rounded-[4px] text-[11px] whitespace-nowrap z-10 transition-opacity pointer-events-none">
                                {day.date}: {formatCurrency(day.cost, data.currency)}
                            </div>
                            <span class="absolute -bottom-[35px] text-[10px] text-google-gray-500 -rotate-45 whitespace-nowrap select-none">{day.date.split('-').slice(1).join('/')}</span>
                        </div>
                    {/each}
                </div>
            </div>
        </div>

        <div class="bg-white border border-google-gray-300 rounded-lg overflow-hidden mb-6">
            <div class="flex justify-between items-center px-4 py-3 border-b border-google-gray-200">
                <h2 class="text-sm font-medium text-google-gray-900 m-0">サービス別内訳 (今月)</h2>
            </div>
            <div class="p-0 overflow-x-auto">
                <table class="w-full text-left text-[13px] text-google-gray-700 border-collapse">
                    <thead class="bg-google-gray-50">
                        <tr>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">サービス名</th>
                            <th class="px-4 py-2.5 border-b border-google-gray-200 font-medium text-google-gray-500 whitespace-nowrap">コスト (今月累計)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {#if !data.serviceCosts || data.serviceCosts.length === 0}
                            <tr><td colspan="2" class="px-4 py-6 text-center text-google-gray-500">データがありません</td></tr>
                        {:else}
                            {#each data.serviceCosts as svc}
                                <tr class="border-b border-google-gray-200 hover:bg-google-gray-50 last:border-b-0">
                                    <td class="px-4 py-3 align-top whitespace-nowrap">{svc.name}</td>
                                    <td class="px-4 py-3 align-top whitespace-nowrap">{formatCurrency(svc.cost, data.currency)}</td>
                                </tr>
                            {/each}
                        {/if}
                    </tbody>
                </table>
            </div>
        </div>
    {:else}
        <div class="bg-[#fce8e6] text-google-red p-3 px-4 rounded-lg text-[13px]">
            課金データの取得に失敗しました。
        </div>
    {/if}
</div>
