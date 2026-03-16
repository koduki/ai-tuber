<script lang="ts">
    import { onMount } from 'svelte';
    import { formatCurrency, formatDate, getTrendIcon } from '$lib/utils/formatters';
    import * as Icons from 'lucide-svelte';

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

    const maxDailyCost = $derived(data?.dailyCosts?.length ? Math.max(...data.dailyCosts.map(d => d.cost)) : 1);
</script>

<div class="billing-container">
    {#if loading}
        <div class="flex items-center justify-center p-12">
            <div class="spinner"></div>
        </div>
    {:else if data}
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-card__label">今月の合計コスト</div>
                <div class="metric-card__value text-blue-600">{data.monthlyCost}</div>
                <div class="metric-card__footer">
                    <span class="metric-card__sub">通貨: {data.currency}</span>
                    <span class="metric-card__trend">{getTrendIcon(data.trend)} {data.trend}</span>
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-card__label">予算設定</div>
                <div class="metric-card__value">{data.budget}</div>
                <div class="metric-card__footer">
                    <span class="metric-card__sub">固定予算</span>
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-card__label">予測 (Forecast)</div>
                <div class="metric-card__value text-gray-400">{data.forecast}</div>
            </div>
        </div>

        <div class="card">
            <div class="card-header">
                <span>日次コスト推移 (直近30日)</span>
                <Icons.BarChart3 size={14} class="text-gray-400" />
            </div>
            <div class="card-body">
                <div class="cost-chart">
                    {#each data.dailyCosts as day}
                        <div class="cost-bar-wrapper group">
                            <div 
                                class="cost-bar" 
                                style="height: {(day.cost / maxDailyCost) * 100}%"
                            ></div>
                            <div class="cost-tooltip group-hover:block hidden">
                                {day.date}: {formatCurrency(day.cost, data.currency)}
                            </div>
                            <span class="cost-bar-label">{day.date.split('-').slice(1).join('/')}</span>
                        </div>
                    {/each}
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-header">
                <span>サービス別内訳 (今月)</span>
                <Icons.PieChart size={14} class="text-gray-400" />
            </div>
            <div class="card-body p-0">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>サービス名</th>
                            <th class="text-right">コスト</th>
                            <th>比率</th>
                        </tr>
                    </thead>
                    <tbody>
                        {#each data.serviceCosts as svc}
                            {@const ratio = (svc.cost / (parseFloat(data.monthlyCost.replace(/[^0-9.-]+/g, "")) || 1)) * 100}
                            <tr>
                                <td class="font-medium">{svc.name}</td>
                                <td class="text-right font-mono">{formatCurrency(svc.cost, data.currency)}</td>
                                <td class="w-1/3">
                                    <div class="flex items-center gap-3">
                                        <div class="flex-1 bg-gray-100 rounded-full h-1.5 overflow-hidden">
                                            <div class="bg-blue-500 h-1.5" style="width: {ratio}%"></div>
                                        </div>
                                        <span class="text-xs text-gray-500 w-8">{ratio.toFixed(1)}%</span>
                                    </div>
                                </td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
        </div>
    {:else}
        <div class="error-message">課金データの取得に失敗しました。</div>
    {/if}
</div>

<style>
  .cost-chart {
    display: flex;
    align-items: flex-end;
    gap: 4px;
    height: 200px;
    padding: 20px 10px 40px;
    border-bottom: 1px solid var(--gray-300);
    margin-bottom: 20px;
    overflow-x: auto;
  }

  .cost-bar-wrapper {
    flex: 1;
    min-width: 25px;
    display: flex;
    flex-direction: column-reverse;
    align-items: center;
    position: relative;
    height: 100%;
  }

  .cost-bar {
    width: 100%;
    background: #c2e7ff;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    transition: height 0.3s ease, background 0.2s;
    cursor: pointer;
    min-height: 2px;
  }

  .cost-bar:hover {
    background: var(--blue);
  }

  .cost-bar-label {
    position: absolute;
    bottom: -30px;
    font-size: 10px;
    color: var(--gray-500);
    transform: rotate(-45deg);
    white-space: nowrap;
  }

  .cost-tooltip {
    position: absolute;
    top: -30px;
    background: #3c4043;
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 11px;
    white-space: nowrap;
    z-index: 10;
  }
</style>
