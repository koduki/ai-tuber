<script lang="ts">
  import { onMount } from 'svelte';
  import * as Icons from 'lucide-svelte';
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
  <div class="flex items-center justify-center h-screen bg-gray-50">
    <div class="text-center">
      <div class="spinner mb-4"></div>
      <div class="text-gray-500 font-medium">Initializing Ops Portal...</div>
    </div>
  </div>
{:else}
  <div class="app-container">
    <header class="header">
      <div class="flex items-center gap-4">
        <button class="icon-btn">
          <Icons.Menu size={20} />
        </button>
        <div class="text-xl font-medium tracking-tight flex items-center">
          <span class="text-blue-600">Google</span>
          <span class="text-gray-500 ml-2 font-normal">Cloud</span>
          <span class="ml-4 text-gray-400 font-light border-l pl-4 border-gray-300">Ops Portal</span>
        </div>
      </div>
      
      <div class="flex items-center gap-4">
        <div class="flex items-center gap-2 px-3 py-1 bg-gray-100 rounded-full text-xs font-medium text-gray-600">
          <Icons.Shield size={14} />
          <span>IAP Protected</span>
        </div>
        <button class="icon-btn" onclick={() => window.location.reload()}>
          <Icons.RefreshCw size={18} />
        </button>
        <div class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 text-xs font-bold border border-blue-200">
          AI
        </div>
      </div>
    </header>

    <div class="main-layout">
      <aside class="sidebar">
        {#each manifest as mod}
          {@const IconComponent = Icons[mod.icon] || Icons.HelpCircle}
          <a
            href="/modules/{mod.id}"
            class="sidebar-item"
            class:active={activeModuleId === mod.id}
          >
            <IconComponent size={18} />
            <span>{mod.title}</span>
          </a>
        {/each}
        
        <div class="mt-auto border-t border-gray-200 pt-4">
          <button 
            class="sidebar-item w-full text-left" 
            onclick={() => window.location.href = '/auth/logout'}
          >
            <Icons.LogOut size={18} />
            <span>ログアウト</span>
          </button>
        </div>
      </aside>
      
      <main class="content-area">
        <div class="mb-6 flex justify-between items-end">
          <div>
            <div class="text-xs text-gray-500 mb-1">AI Tuber Platform / {activeModule.title}</div>
            <h1 class="text-2xl font-normal text-gray-900">{activeModule.title}</h1>
          </div>
          <div class="text-xs text-gray-400">
            Last check: {new Date().toLocaleTimeString('ja-JP')}
          </div>
        </div>
        
        {@render children()}
      </main>
    </div>
  </div>
{/if}

<style>
  /* Local layout specific styles can go here if not in app.css */
</style>
