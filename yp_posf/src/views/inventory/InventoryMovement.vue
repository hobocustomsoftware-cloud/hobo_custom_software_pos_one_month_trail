<template>
  <div class="space-y-6 min-h-full bg-[var(--color-bg)]">
    <div class="flex flex-wrap justify-between items-center" style="gap: var(--fluid-gap);">
      <h1 class="text-fluid-xl font-black uppercase tracking-tight text-[var(--color-fg)]">Stock Movement</h1>
      <button @click="showAddModal = true" class="btn-primary px-6 py-2.5 flex items-center gap-2 interactive">
        <ArrowUpDown class="w-5 h-5" /> RECORD MOVEMENT
      </button>
    </div>

    <FilterDataTable
      ref="tableRef"
      title="Movement History"
      light
      :columns="columns"
      :data="movements"
      :total-count="totalCount"
      :loading="loading"
      search-placeholder="Product, notes ရှာပါ..."
      :default-page-size="20"
      empty-message="လှုပ်ရှားမှု မရှိသေးပါ။"
      @fetch-data="fetchData"
    >
      <template #cell-created_at="{ value }">
        <span class="text-[var(--color-fg-muted)] text-fluid-sm">{{ formatDate(value) }}</span>
      </template>
      <template #cell-product_name="{ value }">
        <span class="font-semibold text-[var(--color-fg)] uppercase text-fluid-sm">{{ value }}</span>
      </template>
      <template #cell-product_unit="{ value }">
        <span class="text-fluid-sm text-[var(--color-fg-muted)]">{{ value || '—' }}</span>
      </template>
      <template #cell-from_location_name="{ row }">
        <div class="flex flex-col gap-0.5">
          <span class="text-[10px] font-bold text-[var(--color-fg-muted)] uppercase">{{ row.to_location_name ? 'Path' : 'Inbound' }}</span>
          <div class="flex items-center gap-1.5 text-fluid-sm">
            <span class="text-[var(--color-fg-muted)]">{{ row.from_location_name || '📦 NEW' }}</span>
            <ArrowRight v-if="row.to_location_name" class="w-3.5 h-3.5 text-[var(--color-fg-muted)]" />
            <span class="text-[var(--color-fg)]">{{ row.to_location_name || '' }}</span>
          </div>
        </div>
      </template>
      <template #cell-movement_type="{ value }">
        <span
          :class="
            value === 'inbound' || value === 'transfer'
              ? 'bg-emerald-100 text-emerald-700 border-emerald-300'
              : 'bg-rose-100 text-rose-700 border-rose-300'
          "
          class="px-3 py-1 rounded-lg text-[10px] font-bold uppercase border"
        >
          {{ value }}
        </span>
      </template>
      <template #cell-quantity="{ row }">
        <span
          class="font-black text-fluid-sm"
          :class="
            row.movement_type === 'inbound' || row.movement_type === 'transfer'
              ? 'text-emerald-600'
              : 'text-rose-600'
          "
        >
          {{ row.movement_type === 'inbound' || row.movement_type === 'transfer' ? '+' : '-' }}{{ row.quantity }}
        </span>
      </template>
    </FilterDataTable>

    <div v-if="showAddModal" class="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="showAddModal = false" />
      <div class="bg-white w-full max-w-2xl p-8 relative z-10 rounded-xl border border-[var(--color-border)] shadow-xl">
        <button
          @click="showAddModal = false"
          class="absolute top-4 right-4 p-2 rounded-xl text-[var(--color-fg-muted)] hover:text-[var(--color-fg)] hover:bg-[var(--color-bg-card)] transition"
        >
          <X class="w-5 h-5" />
        </button>
        <h2 class="text-fluid-xl font-black text-[var(--color-fg)] mb-6 uppercase tracking-tight">Stock Transfer</h2>
        <TransferUI @success="handleSuccess" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ArrowUpDown, ArrowRight, X } from 'lucide-vue-next'
import FilterDataTable from '@/components/FilterDataTable.vue'
import TransferUI from './TransferUI.vue'
import api from '@/services/api'

const tableRef = ref(null)
const movements = ref([])
const totalCount = ref(0)
const loading = ref(false)
const showAddModal = ref(false)

const columns = [
  { key: 'created_at', label: 'Date/Time', sortable: true, type: 'datetime' },
  { key: 'product_name', label: 'Product', sortable: true },
  { key: 'product_unit', label: 'Unit', sortable: false },
  { key: 'from_location_name', label: 'From → To', sortable: false },
  { key: 'movement_type', label: 'Type', sortable: true },
  { key: 'quantity', label: 'Qty', sortable: true },
]

function fetchData({ search, page, pageSize, ordering }) {
  loading.value = true
  const params = { page, page_size: pageSize }
  if (search) params.search = search
  if (ordering) params.ordering = ordering
  api
    .get('movements/', { params })
    .then((res) => {
      movements.value = res.data.results ?? res.data ?? []
      totalCount.value = res.data.count ?? movements.value.length
    })
    .catch(() => {
      movements.value = []
      totalCount.value = 0
    })
    .finally(() => {
      loading.value = false
    })
}

function handleSuccess() {
  showAddModal.value = false
  tableRef.value?.emitFetch()
}

function formatDate(dateStr) {
  if (!dateStr) return '–'
  return new Date(dateStr).toLocaleString('en-GB', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>
