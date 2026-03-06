<template>
  <div class="glass-card overflow-hidden">
    <!-- Header with Search -->
    <div class="p-5 border-b border-[var(--surface-border)] flex flex-wrap items-center justify-between" style="gap: var(--fluid-gap);">
      <h3 class="text-fluid-lg font-bold text-white/90 uppercase tracking-tight">
        {{ title }}
      </h3>
      <div class="flex items-center gap-3">
        <div class="relative">
          <Search class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-white/40" />
          <input
            v-model="searchQuery"
            type="text"
            :placeholder="searchPlaceholder"
            class="glass-input pl-10 pr-4 py-2.5 rounded-xl w-64 lg:w-80 outline-none"
          />
        </div>
        <slot name="header-actions" />
      </div>
    </div>

    <!-- Table -->
    <div class="glass-table-container overflow-x-auto custom-scrollbar">
      <table class="glass-table">
        <thead>
          <tr>
            <th
              v-for="col in columns"
              :key="col.key"
              @click="col.sortable !== false ? sortBy(col.key) : null"
              :class="[
                col.sortable !== false ? 'cursor-pointer hover:text-white transition-colors select-none interactive' : '',
                sortKey === col.key ? 'text-white' : '',
              ]"
            >
              <div class="flex items-center gap-1.5">
                {{ col.label }}
                <ArrowUpDown v-if="col.sortable !== false" class="w-3.5 h-3.5 opacity-60" />
              </div>
            </th>
            <th v-if="$slots.actions" class="text-right">
              Actions
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(row, idx) in paginatedData"
            :key="row.id ?? idx"
            class="interactive"
          >
            <td
              v-for="col in columns"
              :key="col.key"
            >
              <slot :name="`cell-${col.key}`" :row="row" :value="getValue(row, col.key)">
                <span class="text-white/90 font-medium text-fluid-sm">{{ formatValue(getValue(row, col.key), col) }}</span>
              </slot>
            </td>
            <td v-if="$slots.actions" class="text-right">
              <slot name="actions" :row="row" />
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Empty State -->
    <div v-if="filteredData.length === 0" class="p-16 text-center">
      <div class="text-5xl mb-4 opacity-40">📋</div>
      <p class="text-white/50 font-semibold uppercase text-fluid-sm tracking-wider">{{ emptyMessage }}</p>
    </div>

    <!-- Pagination -->
    <div v-if="filteredData.length > 0" class="p-4 border-t border-[var(--surface-border)] flex flex-wrap items-center justify-between" style="gap: var(--fluid-gap);">
      <p class="text-fluid-sm font-medium text-white/60">
        Showing {{ (currentPage - 1) * itemsPerPage + 1 }} - {{ Math.min(currentPage * itemsPerPage, filteredData.length) }} of {{ filteredData.length }}
      </p>
      <div class="flex items-center gap-2">
        <button
          @click="currentPage = Math.max(1, currentPage - 1)"
          :disabled="currentPage === 1"
          class="btn-secondary p-2 disabled:opacity-40 disabled:cursor-not-allowed interactive"
        >
          <ChevronLeft class="w-4 h-4" />
        </button>
        <div class="flex gap-1.5">
          <button
            v-for="p in visiblePages"
            :key="p"
            @click="currentPage = p"
            :class="p === currentPage ? 'bg-[#aa0000] text-white border-[#aa0000] shadow-lg shadow-[#aa0000]/30' : 'glass-surface text-white/70 border-[var(--surface-border)] hover:border-white/20'"
            class="min-w-[36px] h-9 rounded-xl text-fluid-sm font-bold border transition-all duration-300 interactive"
          >
            {{ p }}
          </button>
        </div>
        <button
          @click="currentPage = Math.min(totalPages, currentPage + 1)"
          :disabled="currentPage === totalPages"
          class="btn-secondary p-2 disabled:opacity-40 disabled:cursor-not-allowed interactive"
        >
          <ChevronRight class="w-4 h-4" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Search, ArrowUpDown, ChevronLeft, ChevronRight } from 'lucide-vue-next'

const props = defineProps({
  data: { type: Array, default: () => [] },
  columns: { type: Array, required: true },
  title: { type: String, default: 'Data' },
  searchPlaceholder: { type: String, default: 'Search...' },
  emptyMessage: { type: String, default: 'No data found' },
  itemsPerPage: { type: Number, default: 10 },
  searchKeys: { type: Array, default: null }, // null = search all string values
})

const searchQuery = ref('')
const sortKey = ref(null)
const sortDir = ref('asc')
const currentPage = ref(1)

const getValue = (row, key) => {
  const parts = key.split('.')
  let v = row
  for (const p of parts) v = v?.[p]
  return v
}

const formatValue = (val, col) => {
  if (val == null) return '-'
  if (col.type === 'date') return new Date(val).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
  if (col.type === 'datetime') return new Date(val).toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
  if (col.type === 'currency') return Number(val).toLocaleString() + ' MMK'
  if (col.type === 'number') return Number(val).toLocaleString()
  return String(val)
}

const searchKeysToUse = computed(() => props.searchKeys ?? props.columns.map((c) => c.key))

const filteredData = computed(() => {
  let list = [...props.data]
  const q = searchQuery.value.trim().toLowerCase()
  if (q) {
    list = list.filter((row) =>
      searchKeysToUse.value.some((key) => {
        const v = getValue(row, key)
        return v != null && String(v).toLowerCase().includes(q)
      }),
    )
  }
  if (sortKey.value) {
    list.sort((a, b) => {
      const va = getValue(a, sortKey.value)
      const vb = getValue(b, sortKey.value)
      const cmp = va == null && vb == null ? 0 : (va == null ? 1 : vb == null ? -1 : (va < vb ? -1 : va > vb ? 1 : 0))
      return sortDir.value === 'asc' ? cmp : -cmp
    })
  }
  return list
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredData.value.length / props.itemsPerPage)))

const visiblePages = computed(() => {
  const total = totalPages.value
  const cur = currentPage.value
  const delta = 2
  const range = []
  for (let i = Math.max(1, cur - delta); i <= Math.min(total, cur + delta); i++) range.push(i)
  return range
})

const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * props.itemsPerPage
  return filteredData.value.slice(start, start + props.itemsPerPage)
})

const sortBy = (key) => {
  if (sortKey.value === key) sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  else (sortKey.value = key), (sortDir.value = 'asc')
  currentPage.value = 1
}

watch(searchQuery, () => (currentPage.value = 1))
watch(() => props.data, () => (currentPage.value = 1))
</script>
