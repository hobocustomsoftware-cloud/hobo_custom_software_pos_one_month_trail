<template>
  <!-- Page: white header (title + actions), light main, white cards -->
  <div class="loyverse-page flex flex-col min-h-0 flex-1 w-full">
    <header class="loyverse-header flex-none flex items-center justify-between gap-3 sm:gap-4 px-3 sm:px-4 py-3 min-h-[52px] sm:min-h-[56px] bg-[var(--color-bg-card)] border-b border-[var(--color-border)] shrink-0">
      <h1 class="text-base sm:text-lg font-semibold text-[var(--color-text)] truncate min-w-0">
        {{ title }}
      </h1>
      <div v-if="$slots.actions" class="flex items-center gap-2 flex-wrap shrink-0">
        <slot name="actions" />
      </div>
    </header>

    <div class="loyverse-main flex-1 min-h-0 p-3 sm:p-4 md:p-5 lg:p-6 overflow-auto custom-scrollbar" :style="{ backgroundColor: mainBg || 'var(--color-bg-light)' }">
      <div v-if="card" class="loyverse-card glass-card rounded-xl overflow-hidden flex flex-col min-h-0">
        <slot />
      </div>
      <slot v-else />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, default: '' },
  /** Use #f4f4f4 for Loyverse main area */
  mainBg: { type: String, default: '#f4f4f4' },
  /** Wrap default slot in a single white card */
  card: { type: Boolean, default: true },
})
</script>

<style scoped>
.loyverse-page {
  --loyverse-content-bg: var(--color-bg-light);
  --loyverse-card-bg: var(--color-bg-card);
  --loyverse-text: var(--color-text);
  --loyverse-text-muted: var(--color-text-muted);
  --loyverse-primary: var(--color-primary);
  --loyverse-primary-hover: var(--color-primary-light);
}
.loyverse-card {
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04), 0 2px 6px rgba(0, 0, 0, 0.04);
}
</style>
