<template>
  <div class="skeleton-grid" :style="{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 'var(--fluid-gap, 1rem)' }">
    <div
      v-for="i in count"
      :key="i"
      class="skeleton-card rounded-2xl p-4 border border-white/10 bg-white/5 animate-pulse"
    >
      <div class="h-3 w-1/3 rounded bg-white/20 mb-3" />
      <div class="h-5 w-full rounded bg-white/15 mb-2" />
      <div class="h-6 w-2/3 rounded bg-white/20" />
      <div class="h-4 w-1/4 rounded bg-white/10 mt-3 ml-auto" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  count: { type: Number, default: 6 },
})
</script>

<style scoped>
.skeleton-card {
  min-height: 100px;
}
</style>
