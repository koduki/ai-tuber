# PR #75 Review Plan & Proposed Improvements

## Overview
This PR introduces a much-needed module scaffold template (`dashboard/src/modules/_template/`) and correctly excludes it from dynamic loading via `import.meta.glob` using negative patterns (`!/src/modules/_*/**`). This ensures the template isn't accidentally loaded or exposed via the manifest.

The implementation effectively resolves issue #68 and demonstrates a good understanding of SvelteKit and Vite.

Below is a detailed plan for addressing potential review comments and further improving the template to serve as a high-quality scaffold for future module development.

## Proposed Improvements

### 1. Enhance TypeScript Types and JSDoc Comments
The template serves as a guide for developers. Adding strong typing and descriptive JSDoc comments will significantly improve developer experience.

**`dashboard/src/modules/_template/index.ts`**
Add comments explaining each property.
```typescript
import type { ModuleMetadata } from '../../lib/types/module';

/**
 * Module metadata configuration.
 * This defines how the module appears in the dashboard sidebar and manifest.
 */
export const metadata: ModuleMetadata = {
    title: 'モジュール名',      // The display name shown in the sidebar
    icon: 'LayoutDashboard',   // Lucide-Svelte icon name (ensure it's imported in the main sidebar layout)
    priority: 50               // Sorting order (lower numbers appear higher in the list)
};
```

**`dashboard/src/modules/_template/View.svelte`**
Replace `any` with a specific type or interface to demonstrate typed API responses.
```typescript
<script lang="ts">
    import { onMount } from 'svelte';

    // --- Types ---
    /**
     * Define the expected structure of the API response.
     */
    interface TemplateData {
        message: string;
        // Add other expected fields here
    }

    // --- State ---
    // Use the defined type for the state variable
    let data = $state<TemplateData | null>(null);
    let loading = $state(true);
    let error = $state<string | null>(null); // Added error state

    // ... fetchData implementation (see below)
</script>
```

### 2. Implement Robust Error Handling
Currently, `View.svelte` only logs errors to the console. The template should demonstrate how to display error states to the user. `api.ts` should also show how to return proper HTTP errors.

**`dashboard/src/modules/_template/View.svelte`**
```typescript
    // --- データ取得 ---
    async function fetchData() {
        loading = true;
        error = null; // Reset error state before fetching
        try {
            // Note: In a real module, replace {module-id} dynamically if needed,
            // though typical modules might just call their specific endpoint.
            const res = await fetch('/api/modules/_template/index');

            if (!res.ok) {
                // Handle non-2xx responses
                throw new Error(`API Error: ${res.status} ${res.statusText}`);
            }

            data = await res.json();
        } catch (err: any) {
            console.error('Fetch error:', err);
            error = err.message || 'データの取得に失敗しました。';
        } finally {
            loading = false;
        }
    }
```

Update the template markup to show the error:
```svelte
    {#if loading}
        <div class="text-google-gray-500 text-[13px] text-center py-6">読み込み中...</div>
    {:else if error}
        <!-- エラー表示 -->
        <div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative" role="alert">
            <strong class="font-bold">Error:</strong>
            <span class="block sm:inline">{error}</span>
            <button class="mt-2 text-sm underline cursor-pointer" onclick={fetchData}>再試行</button>
        </div>
    {:else if data}
        <!-- 正常系 UI (既存のカード UI) -->
        ...
```

**`dashboard/src/modules/_template/api.ts`**
Demonstrate how to throw proper SvelteKit errors.
```typescript
import { json, error } from '@sveltejs/kit';
import type { ModuleApi } from '../../lib/types/module';

export const GET: ModuleApi['GET'] = {
    'index': async () => {
        try {
            // TODO: Fetch real data here
            // Example of throwing a 404 error if data isn't found:
            // if (!data) throw error(404, 'Data not found');

            return json({ message: 'Hello from template' });
        } catch (err) {
            // Re-throw SvelteKit errors, or wrap unexpected errors in a 500
            console.error('API execution failed:', err);
            throw error(500, 'Internal Server Error');
        }
    }
};
```

### 3. Add Testing Scaffold
To encourage test-driven development, the template should include a placeholder for tests. This shows developers where and how tests should be written for modules.

**Create `dashboard/src/modules/_template/api.test.ts` (Example using Vitest)**
```typescript
import { describe, it, expect } from 'vitest';
import { GET } from './api';

describe('Template API', () => {
    it('returns hello message', async () => {
        // Example test for the index endpoint
        const response = await GET['index']();
        const data = await response.json();

        expect(response.status).toBe(200);
        expect(data).toEqual({ message: 'Hello from template' });
    });
});
```

### Summary
Implementing these improvements will transform the simple scaffold into a comprehensive guide, ensuring consistency, reliability, and better developer experience as the dashboard ecosystem grows.
