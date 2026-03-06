<template>
  <div class="max-w-2xl mx-auto py-8">
    <h1 class="text-xl font-semibold text-[var(--color-fg)] mb-2">{{ title }}</h1>
    <p class="text-sm text-[var(--color-fg-muted)]">{{ description || 'This section will be connected to the backend API.' }}</p>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  description: { type: String, default: '' },
})
</script>
