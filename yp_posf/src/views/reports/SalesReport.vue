<template>
  <div class="layout-container space-y-6 max-w-[1600px] mx-auto bg-[#f4f4f4] min-h-full" style="gap: var(--fluid-gap);">
    <div class="flex flex-wrap justify-between items-center" style="gap: var(--fluid-gap);">
      <div>
        <h1 class="text-fluid-xl font-black uppercase tracking-tight text-[#1a1a1a]">အရောင်းအစီရင်ခံစာ</h1>
        <p class="text-fluid-sm font-medium text-[#6b7280] uppercase tracking-wider mt-1">Sales Analysis</p>
      </div>
      <button
        @click="tableRef?.emitFetch()"
        :disabled="loading"
        class="btn-primary px-4 py-2.5 flex items-center gap-2 interactive disabled:opacity-70"
      >
        <RefreshCw :class="{ 'animate-spin': loading }" class="w-4 h-4" />
        Refresh
      </button>
    </div>

    <FilterDataTable
      ref="tableRef"
      light
      :data="sales"
      :columns="columns"
      :total-count="totalCount"
      :loading="loading"
      title="Sales History"
      search-placeholder="Invoice, Customer, Status ရှာပါ..."
      :default-page-size="20"
      empty-message="အရောင်းစာရင်း မရှိသေးပါ။"
      @fetch-data="fetchData"
    >
      <template #cell-invoice_number="{ value }">
        <span class="font-mono font-bold text-[#1a1a1a] bg-[var(--color-bg-card)] px-3 py-1.5 rounded-lg border border-[var(--color-border)]">#{{ value || '-' }}</span>
      </template>
      <template #cell-total_amount="{ value }">
        <span class="font-bold text-[#1a1a1a] text-fluid-sm">{{ value != null ? Math.round(Number(value)).toLocaleString(undefined, { maximumFractionDigits: 0 }) + ' MMK' : '-' }}</span>
      </template>
      <template #cell-status="{ value }">
        <span :class="statusClass(value)" class="px-3 py-1.5 rounded-lg text-fluid-sm font-semibold uppercase border">{{ value }}</span>
      </template>
      <template #cell-created_at="{ value }">
        {{ value ? new Date(value).toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '-' }}
      </template>
      <template #actions="{ row }">
        <button
          v-if="row.status === 'approved'"
          @click="openPdf(row.id)"
          class="btn-secondary inline-flex items-center gap-1.5 px-3 py-1.5 text-fluid-sm interactive"
        >
          <FileDown class="w-3.5 h-3.5" /> PDF
        </button>
      </template>
    </FilterDataTable>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import FilterDataTable from '@/components/FilterDataTable.vue'
import { RefreshCw, FileDown } from 'lucide-vue-next'
import api from '@/services/api'

const tableRef = ref(null)
const sales = ref([])
const totalCount = ref(0)
const loading = ref(false)

const columns = [
  { key: 'invoice_number', label: 'Invoice No', sortable: true },
  { key: 'created_at', label: 'Date', sortable: true, type: 'datetime' },
  { key: 'customer_name', label: 'Customer', sortable: true },
  { key: 'location_name', label: 'Location', sortable: true },
  { key: 'total_amount', label: 'Total', sortable: true, type: 'currency' },
  { key: 'status', label: 'Status', sortable: true },
]

const statusClass = (s) => {
  const st = (s || '').toLowerCase()
  if (st === 'approved') return 'bg-emerald-500/20 text-emerald-300 border border-emerald-400/30'
  if (st === 'pending') return 'bg-amber-500/20 text-amber-300 border border-amber-400/30'
  if (st === 'rejected') return 'bg-rose-500/20 text-rose-300 border border-rose-400/30'
  return 'bg-gray-500/20 text-gray-300 border border-gray-400/30'
}

function fetchData({ search, page, pageSize, ordering }) {
  loading.value = true
  const params = { page, page_size: pageSize }
  if (search) params.search = search
  if (ordering) params.ordering = ordering
  api
    .get('invoices/', { params })
    .then((res) => {
      sales.value = res.data.results ?? res.data ?? []
      totalCount.value = res.data.count ?? sales.value.length
    })
    .catch(() => {
      sales.value = []
      totalCount.value = 0
    })
    .finally(() => {
      loading.value = false
    })
}

const openPdf = async (id) => {
  try {
    const res = await api.get('invoice/' + id + '/pdf/', { responseType: 'blob' })
    const url = URL.createObjectURL(res.data)
    window.open(url, '_blank')
  } catch (e) {
    console.error(e)
    alert('PDF ထုတ်ယူခြင်း မအောင်မြင်ပါ။')
  }
}
</script>
