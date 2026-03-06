<template>
  <div
    class="flex flex-wrap items-center justify-between gap-3 py-3 px-4 border-t border-white/10"
    :class="wrapperClass"
  >
    <div class="flex items-center gap-2 text-xs text-white/60">
      <span v-if="totalItems > 0">
        {{ (currentPage - 1) * pageSize + 1 }}-{{ Math.min(currentPage * pageSize, totalItems) }}
        of {{ totalItems }}
      </span>
      <span v-else>0 results</span>
    </div>
    <div class="flex items-center gap-1">
      <button
        type="button"
        :disabled="currentPage <= 1"
        class="p-2 rounded-xl glass-input hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
        aria-label="Previous page"
        @click="$emit('update:currentPage', currentPage - 1)"
      >
        <ChevronLeft class="w-4 h-4 text-white/70" :stroke-width="1.5" />
      </button>
      <template v-for="p in visiblePages" :key="p">
        <button
          v-if="p !== '...'"
          type="button"
          :class="
            currentPage === p
              ? 'bg-white/20 text-white border-white/30'
              : 'bg-white/5 text-white/70 border-white/20 hover:bg-white/10'
          "
          class="min-w-[2.25rem] h-9 rounded-xl text-xs font-bold border transition-all"
          @click="$emit('update:currentPage', p)"
        >
          {{ p }}
        </button>
        <span v-else class="px-1 text-white/40">…</span>
      </template>
      <button
        type="button"
        :disabled="currentPage >= totalPages"
        class="p-2 rounded-xl glass-input hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
        aria-label="Next page"
        @click="$emit('update:currentPage', currentPage + 1)"
      >
        <ChevronRight class="w-4 h-4 text-white/70" :stroke-width="1.5" />
      </button>
    </div>
    <div v-if="showSizePicker" class="flex items-center gap-2">
      <label class="text-xs text-white/50">Per page</label>
      <select
        :value="pageSize"
        class="glass-input rounded-lg px-2 py-1 text-xs text-white/90 outline-none"
        @change="$emit('update:pageSize', Number($event.target.value))"
      >
        <option v-for="s in pageSizeOptions" :key="s" :value="s">{{ s }}</option>
      </select>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'

const props = withDefaults(
  defineProps({
    currentPage: { type: Number, required: true },
    totalPages: { type: Number, required: true },
    totalItems: { type: Number, default: 0 },
    pageSize: { type: Number, default: 10 },
    pageSizeOptions: { type: Array, default: () => [10, 20, 50, 100] },
    showSizePicker: { type: Boolean, default: true },
    maxVisiblePages: { type: Number, default: 5 },
    wrapperClass: { type: String, default: '' },
  }),
)

defineEmits(['update:currentPage', 'update:pageSize'])

const visiblePages = computed(() => {
  const total = props.totalPages
  if (total <= props.maxVisiblePages) {
    return Array.from({ length: total }, (_, i) => i + 1)
  }
  const cur = props.currentPage
  const half = Math.floor(props.maxVisiblePages / 2)
  let start = Math.max(1, cur - half)
  let end = Math.min(total, start + props.maxVisiblePages - 1)
  if (end - start + 1 < props.maxVisiblePages) start = Math.max(1, end - props.maxVisiblePages + 1)
  const pages = []
  if (start > 1) {
    pages.push(1)
    if (start > 2) pages.push('...')
  }
  for (let i = start; i <= end; i++) pages.push(i)
  if (end < total) {
    if (end < total - 1) pages.push('...')
    pages.push(total)
  }
  return pages
})
</script>
