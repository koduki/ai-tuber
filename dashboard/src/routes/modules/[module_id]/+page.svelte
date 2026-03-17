<script lang="ts">
  import { page } from '$app/state';
  
  const views = import.meta.glob('/src/modules/*/View.svelte');
  
  let module_id = $derived(page.params.module_id);
  let viewPromise = $derived(views[`/src/modules/${module_id}/View.svelte`]?.().then((m: any) => m.default));
</script>

{#if viewPromise}
  {#await viewPromise}
    <div class="p-8 flex items-center justify-center h-full">
        <div class="text-xl text-gray-500">Loading module {module_id}...</div>
    </div>
  {:then Component}
    {#if Component}
      <Component />
    {:else}
      <div class="p-8 text-red-500">View component failed to load for {module_id}.</div>
    {/if}
  {:catch error}
    <div class="p-8 text-red-500">Error loading module: {error.message}</div>
  {/await}
{:else}
  <div class="p-8 text-red-500 h-full flex items-center justify-center">
    <div class="text-center">
        <h2 class="text-2xl font-bold mb-2">Module Not Found</h2>
        <p class="text-gray-600">The requested module "{module_id}" could not be located.</p>
    </div>
  </div>
{/if}
