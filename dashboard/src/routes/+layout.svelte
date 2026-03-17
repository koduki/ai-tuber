<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/state';
  import '../app.css';

  let { children } = $props();
  
  let manifest = $state<any[]>([]);
  let loading = $state(true);
  
  onMount(async () => {
    try {
      const res = await fetch('/api/manifest');
      manifest = await res.json();
    } catch (err) {
      console.error('Failed to fetch manifest:', err);
    } finally {
      loading = false;
    }
  });

  let activeModuleId = $derived(page.url.pathname.split('/')[2] || null);
  let activeModule = $derived(manifest.find(m => m.id === activeModuleId) || { title: '概要' });
</script>

<svelte:head>
    <title>AI Tuber IDP - {activeModule.title}</title>
</svelte:head>

{#if loading}
  <div class="flex items-center justify-center min-h-screen">
    <div class="text-center">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-google-blue mx-auto mb-4"></div>
      <div class="text-google-gray-500 font-medium">Initializing Ops Portal...</div>
    </div>
  </div>
{:else}
<!-- ===== Header ===== -->
<header class="sticky top-0 z-20 flex items-center gap-3 h-14 px-4 bg-white border-b border-google-gray-300 w-full">
  <div class="flex items-center gap-[3px] text-[22px] font-medium tracking-tight">
    <span class="text-[#4285F4]">G</span><span class="text-[#DB4437]">o</span><span class="text-[#F4B400]">o</span><span class="text-[#4285F4]">g</span><span class="text-[#0F9D58]">l</span><span class="text-[#DB4437]">e</span>
    <span class="ml-1.5 font-normal text-google-gray-500">Cloud</span>
  </div>
  <div class="ml-auto flex items-center gap-1">
    <button class="w-9 h-9 grid place-items-center rounded-full text-google-gray-500 hover:bg-google-gray-100 transition-colors">?</button>
    <button class="w-9 h-9 grid place-items-center rounded-full text-google-gray-500 hover:bg-google-gray-100 transition-colors">⋮</button>
    <div class="ml-1 w-8 h-8 grid place-items-center rounded-full bg-[#c2e7ff] text-[12px] font-medium text-google-blue-dark">K</div>
  </div>
</header>

<div class="flex flex-col min-h-[calc(100vh-56px)]">
  <main class="flex-1 w-full min-w-0">
    <!-- Page Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 p-4 md:px-6 bg-white border-b border-google-gray-300">
      <div>
        <div class="text-xs text-google-gray-500 mb-1">ホーム / Internal Developer Portal / <span id="project-id">ren-studio-ai</span></div>
        <div class="flex items-center gap-3 mt-1">
          <h1 class="text-[28px] font-normal text-google-gray-900 leading-[1] m-0">AI Tuber Platform</h1>
          <span class="rounded-full px-3 py-1 text-xs font-medium bg-google-green-bg text-google-green">正常</span>
        </div>
        <p class="text-[13px] text-google-gray-500 mt-2 m-0">定期実行、ワークフロー、稼働リソース、コストを確認する運用ポータル</p>
      </div>
      <div class="flex flex-wrap gap-2">
        <button class="inline-block border border-google-gray-300 bg-white text-google-blue rounded-full px-4 py-2 text-[13px] font-medium hover:bg-[#f8fbff] transition-colors" onclick={() => window.location.reload()}>更新</button>
        <a class="inline-block bg-google-blue text-white rounded-full px-4 py-2 text-[13px] font-medium hover:bg-google-blue-hover transition-colors no-underline" href="https://console.cloud.google.com" target="_blank" rel="noopener">GCP Console を開く</a>
      </div>
    </div>

    <!-- Tabs -->
    <nav class="flex overflow-x-auto px-6 bg-white border-b border-google-gray-300 pt-3 gap-1">
      {#each manifest as mod}
        <a 
          href="/modules/{mod.id}"
          class="px-4 py-2 text-[13px] border border-transparent border-b-0 rounded-t-lg transition-colors whitespace-nowrap no-underline {activeModuleId === mod.id ? 'border-google-gray-300 bg-google-gray-50 text-google-blue relative z-10' : 'text-google-gray-500 hover:bg-google-gray-50'}"
          style="{activeModuleId === mod.id ? 'margin-bottom: -1px; border-bottom-color: var(--color-google-gray-50);' : ''}"
        >
          {mod.title}
        </a>
      {/each}
    </nav>

    <!-- Content Area -->
    <div class="p-6">
      {@render children()}
    </div>
  </main>
</div>
{/if}
