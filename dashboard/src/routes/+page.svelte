<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';

  onMount(() => {
    goto('/modules/overview');
  });
</script>

<div class="h-full flex items-center justify-center">
    <div class="text-gray-400">Loading platform...</div>
</div>
