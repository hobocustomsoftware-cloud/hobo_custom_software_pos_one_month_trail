<template>
  <div class="overflow-hidden" :class="light ? 'rounded-xl border border-[var(--color-border)] bg-white shadow-sm' : 'glass-card'">
    <div class="p-5 border-b flex flex-wrap items-center justify-between gap-4" :class="light ? 'border-[var(--color-border)]' : 'border-[var(--surface-border)]'">
      <h3 class="text-lg font-semibold" :class="light ? 'text-[#1a1a1a]' : 'text-fluid-lg font-bold text-white/90 uppercase tracking-tight'">
        {{ title }}
      </h3>
      <div class="flex items-center gap-3">
        <div class="relative">
          <Search class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2" :class="light ? 'text-[var(--color-fg-muted)]' : 'text-white/40'" />
          <input
            v-model="searchInput"
            type="text"
            :placeholder="searchPlaceholder"
            class="pl-10 pr-4 py-2.5 rounded-xl w-64 lg:w-80 outline-none border border-[var(--color-border)] bg-white text-[#1a1a1a]"
          />
        </div>
        <slot name="header-actions" />
      </div>
    </div>

    <div v-if="loading" class="p-12 flex items-center justify-center">
      <div class="animate-spin w-10 h-10 border-2 rounded-full" :class="light ? 'border-[var(--loyverse-blue)] border-t-transparent' : 'border-[#aa0000] border-t-transparent'" />
    </div>

    <div v-else class="overflow-x-auto">
      <table class="w-full min-w-[600px]" :class="light ? 'data-table-light-table' : 'glass-table'">
        <thead>
          <tr>
            <th
              v-for="col in columns"
              :key="col.key"
              @click="col.sortable !== false ? requestSort(col.key) : null"
              :class="[
                'text-left py-3 px-4 text-sm font-medium',
                col.sortable !== false ? 'cursor-pointer select-none' : '',
                light ? 'text-[var(--color-fg-muted)] bg-[var(--color-bg-card)] border-b border-[var(--color-border)] hover:text-[var(--loyverse-blue)]' : 'hover:text-white',
                !light && (orderKey === col.key ? 'text-white' : ''),
              ]"
            >
              <div class="flex items-center gap-1.5">
                {{ col.label }}
                <ArrowUpDown v-if="col.sortable !== false" class="w-3.5 h-3.5 opacity-60" />
              </div>
            </th>
            <th v-if="$slots.actions" class="text-right py-3 px-4 text-sm font-medium" :class="light ? 'text-[var(--color-fg-muted)] bg-[var(--color-bg-card)] border-b border-[var(--color-border)]' : ''">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, idx) in data" :key="row.id ?? idx" :class="light ? 'border-b border-[var(--color-border)] hover:bg-[var(--color-bg-card)]' : 'interactive'">
            <td v-for="col in columns" :key="col.key" :class="light ? 'py-3 px-4 text-[#1a1a1a]' : ''">
              <slot :name="`cell-${col.key}`" :row="row" :value="getValue(row, col.key)">
                <span class="font-medium text-sm" :class="light ? 'text-[#1a1a1a]' : 'text-white/90 text-fluid-sm'">{{ formatValue(getValue(row, col.key), col) }}</span>
              </slot>
            </td>
            <td v-if="$slots.actions" class="text-right" :class="light ? 'py-3 px-4' : ''">
              <slot name="actions" :row="row" />
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="!loading && data.length === 0" class="p-16 text-center">
      <div class="text-5xl mb-4 opacity-40">📋</div>
      <p class="text-sm font-medium" :class="light ? 'text-[var(--color-fg-muted)]' : 'text-white/50 font-semibold uppercase text-fluid-sm tracking-wider'">{{ emptyMessage }}</p>
    </div>

    <div
      v-if="totalCount > 0"
      class="p-4 border-t flex flex-wrap items-center justify-between gap-4"
      :class="light ? 'border-[var(--color-border)] text-[var(--color-fg-muted)] text-sm' : 'border-[var(--surface-border)] text-fluid-sm font-medium text-white/60'"
    >
      <p>
        Showing {{ (page - 1) * pageSize + 1 }}–{{ Math.min(page * pageSize, totalCount) }} of {{ totalCount }}
      </p>
      <div class="flex items-center gap-3 flex-wrap">
        <label class="flex items-center gap-2 text-sm" :class="light ? 'text-[var(--color-fg-muted)]' : 'text-white/70'">
          <span>Per page</span>
          <select
            v-model="pageSize"
            class="py-1.5 px-2 rounded-lg text-sm outline-none border border-[var(--color-border)] bg-white text-[#1a1a1a]"
            @change="onPageSizeChange"
          >
            <option v-for="n in pageSizeOptions" :key="n" :value="n">{{ n }}</option>
          </select>
        </label>
        <div class="flex items-center gap-2">
          <button
            :disabled="page <= 1"
            class="p-2 rounded-lg border disabled:opacity-40 disabled:cursor-not-allowed"
            :class="light ? 'border-[var(--color-border)] text-[#1a1a1a] hover:bg-[var(--color-bg-card)]' : 'btn-secondary interactive'"
            @click="setPage(page - 1)"
          >
            <ChevronLeft class="w-4 h-4" />
          </button>
          <div class="flex gap-1.5">
            <button
              v-for="p in visiblePages"
              :key="p"
              :class="[
                'min-w-[36px] h-9 rounded-xl text-sm font-bold border transition-all',
                p === page && light ? 'bg-[var(--loyverse-blue)] text-white border-[var(--loyverse-blue)]' : '',
                p === page && !light ? 'bg-[#aa0000] text-white border-[#aa0000] shadow-lg shadow-[#aa0000]/30' : '',
                p !== page && light ? 'border-[var(--color-border)] text-[#1a1a1a] bg-white hover:border-[var(--loyverse-blue)]' : '',
                p !== page && !light ? 'glass-surface text-white/70 border-[var(--surface-border)] hover:border-white/20' : '',
              ]"
              class="interactive"
              @click="setPage(p)"
            >
              {{ p }}
            </button>
          </div>
          <button
            :disabled="page >= totalPages"
            class="p-2 rounded-lg border disabled:opacity-40 disabled:cursor-not-allowed"
            :class="light ? 'border-[var(--color-border)] text-[#1a1a1a] hover:bg-[var(--color-bg-card)]' : 'btn-secondary interactive'"
            @click="setPage(page + 1)"
          >
            <ChevronRight class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { Search, ArrowUpDown, ChevronLeft, ChevronRight } from 'lucide-vue-next'

const props = defineProps({
  title: { type: String, default: 'Data' },
  columns: { type: Array, required: true },
  data: { type: Array, default: () => [] },
  totalCount: { type: Number, default: 0 },
  loading: { type: Boolean, default: false },
  searchPlaceholder: { type: String, default: 'Search...' },
  emptyMessage: { type: String, default: 'No data found' },
  pageSizeOptions: { type: Array, default: () => [10, 20, 50, 100] },
  defaultPageSize: { type: Number, default: 20 },
  debounceMs: { type: Number, default: 350 },
  /** Loyverse-style light theme (white card, black text) */
  light: { type: Boolean, default: false },
})

const emit = defineEmits(['fetch-data'])

const searchInput = ref('')
const page = ref(1)
const pageSize = ref(props.defaultPageSize)
const orderKey = ref(null)
const orderDir = ref('asc')

let debounceTimer = null
const searchQuery = ref('')

function commitSearch() {
  searchQuery.value = searchInput.value.trim()
  page.value = 1
  emitFetch()
}

watch(searchInput, () => {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(commitSearch, props.debounceMs)
})

const totalPages = computed(() => Math.max(1, Math.ceil(props.totalCount / pageSize.value)))

const visiblePages = computed(() => {
  const total = totalPages.value
  const cur = page.value
  const delta = 2
  const range = []
  for (let i = Math.max(1, cur - delta); i <= Math.min(total, cur + delta); i++) range.push(i)
  return range
})

function setPage(p) {
  page.value = Math.max(1, Math.min(p, totalPages.value))
  emitFetch()
}

function onPageSizeChange() {
  page.value = 1
  emitFetch()
}

function requestSort(key) {
  if (orderKey.value === key) orderDir.value = orderDir.value === 'asc' ? 'desc' : 'asc'
  else (orderKey.value = key), (orderDir.value = 'asc')
  page.value = 1
  emitFetch()
}

function emitFetch() {
  emit('fetch-data', {
    search: searchQuery.value,
    page: page.value,
    pageSize: pageSize.value,
    ordering: orderKey.value ? (orderDir.value === 'desc' ? `-${orderKey.value}` : orderKey.value) : undefined,
  })
}

function getValue(row, key) {
  const parts = key.split('.')
  let v = row
  for (const p of parts) v = v?.[p]
  return v
}

function formatValue(val, col) {
  if (val == null) return '-'
  if (col.type === 'date') return new Date(val).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
  if (col.type === 'datetime') return new Date(val).toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
  if (col.type === 'currency') return Math.round(Number(val) || 0).toLocaleString(undefined, { maximumFractionDigits: 0, minimumFractionDigits: 0 }) + ' MMK'
  if (col.type === 'number') return Math.round(Number(val) || 0).toLocaleString(undefined, { maximumFractionDigits: 0, minimumFractionDigits: 0 })
  return String(val)
}

function setSearchAndFetch(q) {
  searchInput.value = q
  searchQuery.value = q
  page.value = 1
  emitFetch()
}

onMounted(() => emitFetch())

defineExpose({ emitFetch, setSearchAndFetch })
</script>
