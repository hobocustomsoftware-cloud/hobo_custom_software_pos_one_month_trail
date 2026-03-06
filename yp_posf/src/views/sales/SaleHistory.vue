<template>
  <div class="min-h-0 font-sans bg-[#f4f4f4]">
    <div class="layout-container max-w-7xl mx-auto">
      <div class="flex flex-wrap justify-between items-center mb-6" style="gap: var(--fluid-gap);">
        <div>
          <h1 class="text-fluid-xl font-black uppercase tracking-tight text-[#1a1a1a]">My Sale History</h1>
          <p class="text-fluid-sm font-medium text-[#6b7280] uppercase mt-1">
            Admin မှ အတည်ပြုပြီးသော စာရင်းများအား Invoice ထုတ်ယူရန်
          </p>
        </div>
        <button @click="tableRef?.emitFetch()" class="btn-secondary px-4 py-2.5 flex items-center gap-2 interactive">
          <span>🔄</span> Refresh
        </button>
      </div>

      <FilterDataTable
        ref="tableRef"
        title="Sale History"
        light
        :columns="columns"
        :data="mySales"
        :total-count="totalCount"
        :loading="loading"
        search-placeholder="Invoice, Customer ရှာပါ..."
        :default-page-size="20"
        empty-message="ရောင်းချထားသော စာရင်းမရှိသေးပါ။"
        @fetch-data="fetchSales"
      >
        <template #cell-invoice_number="{ value }">
          <div class="px-3 py-1.5 rounded-lg font-mono text-fluid-sm font-black inline-block bg-[var(--color-bg-card)] border border-[var(--color-border)] text-[#1a1a1a]">
            #{{ value || '-' }}
          </div>
        </template>
        <template #cell-created_at="{ value }">
          <span class="text-fluid-sm font-medium text-[#4b5563]">{{ formatDate(value) }}</span>
        </template>
        <template #cell-customer_name="{ row }">
          <div class="text-fluid-base font-semibold text-[#1a1a1a]">{{ row.customer_name || 'Cash Customer' }}</div>
          <div class="text-fluid-sm text-[#6b7280] font-medium">{{ row.customer_phone || '-' }}</div>
        </template>
        <template #cell-total_amount="{ value }">
          <span class="text-fluid-sm font-semibold text-[#1a1a1a]">{{ value != null ? Math.round(Number(value)).toLocaleString(undefined, { maximumFractionDigits: 0 }) + ' MMK' : '—' }}</span>
        </template>
        <template #cell-status="{ value }">
          <span :class="statusBadgeClass(value)" class="px-3 py-1.5 rounded-lg text-fluid-sm font-semibold uppercase">{{ value }}</span>
        </template>
        <template #actions="{ row }">
          <button
            v-if="row.status === 'approved'"
            @click="printInvoice(row)"
            class="btn-primary px-4 py-2 text-fluid-sm flex items-center gap-2 mx-auto"
          >
            <span>🖨️</span> Print A5 Invoice
          </button>
          <div v-else class="flex flex-col items-center gap-1">
            <span class="w-2 h-2 bg-amber-400 rounded-full animate-pulse"></span>
            <span class="text-fluid-sm font-semibold text-amber-400 uppercase">Pending</span>
          </div>
        </template>
      </FilterDataTable>
    </div>
    <InvoicePrint :sale="selectedSale" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import InvoicePrint from '@/components/InvoicePrint.vue'
import FilterDataTable from '@/components/FilterDataTable.vue'
import api from '@/services/api'

const tableRef = ref(null)
const mySales = ref([])
const totalCount = ref(0)
const loading = ref(false)
const selectedSale = ref(null)

const columns = [
  { key: 'invoice_number', label: 'Invoice No', sortable: true },
  { key: 'created_at', label: 'Date', sortable: true, type: 'datetime' },
  { key: 'customer_name', label: 'Customer Info', sortable: true },
  { key: 'total_amount', label: 'Total (MMK)', sortable: true },
  { key: 'status', label: 'Status', sortable: true },
]

function fetchSales({ search, page, pageSize, ordering }) {
  loading.value = true
  const params = { page, page_size: pageSize }
  if (search) params.search = search
  if (ordering) params.ordering = ordering
  api
    .get('sales/history/', { params })
    .then((res) => {
      mySales.value = res.data.results ?? res.data ?? []
      totalCount.value = res.data.count ?? mySales.value.length
    })
    .catch(() => {
      mySales.value = []
      totalCount.value = 0
    })
    .finally(() => {
      loading.value = false
    })
}

const printInvoice = async (sale) => {
  try {
    const res = await api.get(`invoice/${sale.id}/`)
    selectedSale.value = res.data
    setTimeout(() => window.print(), 500)
  } catch (err) {
    console.error('Print Error:', err)
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const statusBadgeClass = (status) => {
  const base = 'px-3 py-1.5 rounded-lg text-fluid-sm font-semibold uppercase tracking-wider border '
  if (status === 'approved') return base + 'bg-emerald-500/20 text-emerald-300 border-emerald-400/30'
  return base + 'bg-amber-500/20 text-amber-300 border-amber-400/30'
}
</script>

<style scoped>
@media print {
  body { visibility: hidden !important; }
  nav, aside, .sidebar, header, .no-print, button { display: none !important; }
  #invoice-print-area, #invoice-print-area * { visibility: visible !important; }
  #invoice-print-area {
    position: absolute !important;
    left: 0 !important;
    top: 0 !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
  }
  @page { size: A5 landscape; margin: 0.5cm; }
}
</style>
