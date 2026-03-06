<template>
  <div v-if="suggestions.length > 0" class="glass-card p-5 rounded-2xl border border-[var(--surface-border)] glow-effect">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-bold text-white flex items-center gap-2">
        <span class="text-2xl">💡</span>
        <span>Compatible Products</span>
      </h3>
      <button
        @click="$emit('close')"
        class="text-white/60 hover:text-white transition-colors"
        v-if="showClose"
      >
        ✕
      </button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="(item, idx) in suggestions"
        :key="idx"
        class="glass-surface p-4 rounded-xl border border-[var(--surface-border)] hover:border-[#aa0000]/50 transition-all duration-300 hover:shadow-lg hover:shadow-[#aa0000]/20"
      >
        <div class="flex items-start justify-between mb-2">
          <div class="flex-1">
            <h4 class="font-bold text-white mb-1 text-sm">{{ item.product.name }}</h4>
            <p class="text-xs text-white/60 mb-2">{{ item.reason }}</p>
            <div class="flex items-center gap-2 mb-2">
              <span class="px-2 py-1 bg-[#aa0000]/20 text-[#aa0000] rounded text-xs font-bold">
                {{ item.type === 'tag_match' ? 'Tag Match' : item.type === 'best_seller' ? 'အရောင်းရဆုံး' : 'Spec Match' }}
              </span>
              <span class="text-xs text-white/40">Score: {{ item.score }}</span>
            </div>
            <div class="text-lg font-bold text-[#aa0000]">
              {{ Number(item.product.retail_price).toLocaleString() }} MMK
            </div>
          </div>
        </div>
        <button
          @click="$emit('add', item.product)"
          class="w-full btn-primary py-2 mt-3 interactive text-sm"
        >
          Quick Add
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  suggestions: {
    type: Array,
    default: () => [],
  },
  showClose: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['close', 'add'])
</script>

<style scoped>
.glow-effect {
  box-shadow: 0 0 20px rgba(170, 0, 0, 0.1);
  animation: pulse-glow 3s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% {
    box-shadow: 0 0 20px rgba(170, 0, 0, 0.1);
  }
  50% {
    box-shadow: 0 0 30px rgba(170, 0, 0, 0.2);
  }
}
</style>
