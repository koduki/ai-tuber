<script lang="ts">
    import { onMount } from 'svelte';
    import { getStatusClass } from '$lib/utils/formatters';
    import { getConsoleUrl } from '$lib/utils/consoleLinks';

    // --- State ---
    let data = $state<any>(null);
    let loading = $state(true);

    // --- データ取得 ---
    async function fetchData() {
        loading = true;
        try {
            const res = await fetch('/api/modules/{module-id}/index');
            data = await res.json();
        } catch (err) {
            console.error('Fetch error:', err);
        } finally {
            loading = false;
        }
    }

    onMount(fetchData);
</script>

<div>
    {#if loading}
        <div class="text-google-gray-500 text-[13px] text-center py-6">読み込み中...</div>
    {:else}
        <!-- カード型のコンテンツ表示 -->
        <div class="bg-white border border-google-gray-300 rounded-lg overflow-hidden">
            <div class="flex justify-between items-center px-4 py-3 border-b border-google-gray-200">
                <h2 class="text-sm font-medium text-google-gray-900 m-0">セクションタイトル</h2>
                <button class="bg-white border-0 text-google-blue text-xs font-medium cursor-pointer hover:underline" onclick={fetchData}>
                    更新
                </button>
            </div>
            <div class="p-4">
                <!-- TODO: UI を実装 -->
                <pre>{JSON.stringify(data, null, 2)}</pre>
            </div>
        </div>
    {/if}
</div>
