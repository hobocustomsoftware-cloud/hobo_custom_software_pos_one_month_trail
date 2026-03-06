<template>
  <div class="w-full max-w-6xl mx-auto px-2 sm:px-4 space-y-4">
    <h1 class="text-lg sm:text-xl font-semibold text-[var(--color-fg)]">Receipts</h1>
    <p class="text-sm text-[var(--color-fg-muted)]">List and reprint receipts.</p>

    <div class="bg-white rounded-xl shadow-sm overflow-hidden min-h-[min(400px,55vh)]">
      <div v-if="loading" class="p-8 text-center text-[var(--color-fg-muted)]">Loading...</div>
      <FilterDataTable
        v-else
        ref="tableRef"
        :data="receipts"
        :columns="columns"
        :total-count="totalCount"
        :loading="loading"
        title="Receipts"
        search-placeholder="Invoice, Customer..."
        :default-page-size="20"
        :light="true"
        empty-message="Receipt မရှိသေးပါ။"
        @fetch-data="doFetch"
      >
        <template #cell-invoice_number="{ value }">
          <span class="font-mono font-medium">#{{ value || '-' }}</span>
        </template>
        <template #cell-total_amount="{ value }">
          <span class="font-medium">{{ value != null ? Math.round(Number(value)).toLocaleString(undefined, { maximumFractionDigits: 0 }) + ' MMK' : '-' }}</span>
        </template>
        <template #cell-status="{ value }">
          <span :class="statusClass(value)" class="px-2 py-1 rounded text-xs font-medium">{{ value }}</span>
        </template>
        <template #cell-created_at="{ value }">
          {{ value ? new Date(value).toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '-' }}
        </template>
        <template #actions="{ row }">
          <button type="button" @click="openDetail(row)" class="text-[var(--color-primary)] hover:underline text-sm mr-2">View</button>
          <button type="button" @click="reprint(row)" class="text-[var(--color-primary)] hover:underline text-sm">Reprint</button>
        </template>
      </FilterDataTable>
    </div>

    <!-- Detail modal -->
    <div v-if="detailInvoice" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" @click.self="detailInvoice = null">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-hidden flex flex-col" @click.stop>
        <div class="p-4 flex justify-between items-center border-b border-[var(--color-border)]">
          <h2 class="text-lg font-semibold">Receipt #{{ detailInvoice.invoice_number }}</h2>
          <button type="button" @click="detailInvoice = null" class="p-2 rounded-lg hover:bg-[var(--color-bg-light)]">✕</button>
        </div>
        <div class="p-4 overflow-y-auto flex-1 text-sm space-y-2">
          <p><span class="text-[var(--color-fg-muted)]">Date:</span> {{ detailInvoice.created_at ? new Date(detailInvoice.created_at).toLocaleString() : '-' }}</p>
          <p><span class="text-[var(--color-fg-muted)]">Customer:</span> {{ detailInvoice.customer_name || '-' }}</p>
          <p><span class="text-[var(--color-fg-muted)]">Location:</span> {{ detailInvoice.location_name || '-' }}</p>
          <p><span class="text-[var(--color-fg-muted)]">Total:</span> {{ detailInvoice.total_amount != null ? Math.round(Number(detailInvoice.total_amount)).toLocaleString() + ' MMK' : '-' }}</p>
          <p><span class="text-[var(--color-fg-muted)]">Status:</span> {{ detailInvoice.status }}</p>
          <div v-if="(detailInvoice.sale_items || []).length" class="mt-4">
            <p class="font-medium mb-2">Items</p>
            <ul class="space-y-1">
              <li v-for="(item, i) in detailInvoice.sale_items" :key="i">{{ item.product_name || 'Item' }} × {{ item.quantity }} — {{ item.subtotal != null ? Math.round(Number(item.subtotal)).toLocaleString() : '-' }} MMK</li>
            </ul>
          </div>
        </div>
        <div class="p-4 border-t border-[var(--color-border)] flex gap-2">
          <button type="button" @click="reprint(detailInvoice)" class="flex-1 btn-primary py-2">Reprint / PDF</button>
          <button type="button" @click="detailInvoice = null" class="flex-1 btn-secondary py-2">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import FilterDataTable from '@/components/FilterDataTable.vue'
import api from '@/services/api'

const tableRef = ref(null)
const receipts = ref([])
const totalCount = ref(0)
const loading = ref(true)
const detailInvoice = ref(null)
const lastFetchAt = ref(0)
const THROTTLE_MS = 2000

const columns = [
  { key: 'invoice_number', label: 'Invoice No', sortable: true },
  { key: 'created_at', label: 'Date', sortable: true, type: 'datetime' },
  { key: 'customer_name', label: 'Customer', sortable: true },
  { key: 'location_name', label: 'Location', sortable: true },
  { key: 'total_amount', label: 'Total', sortable: true },
  { key: 'status', label: 'Status', sortable: true },
]

function statusClass(s) {
  const st = (s || '').toLowerCase()
  if (st === 'approved') return 'bg-emerald-100 text-emerald-800'
  if (st === 'pending') return 'bg-amber-100 text-amber-800'
  if (st === 'rejected') return 'bg-red-100 text-red-800'
  return 'bg-gray-100 text-gray-700'
}

function doFetch(opts = {}) {
  const now = Date.now()
  if (!opts.force && now - lastFetchAt.value < THROTTLE_MS) return
  lastFetchAt.value = now
  loading.value = true
  const params = { page: opts.page || 1, page_size: opts.pageSize || 20, status: 'approved' }
  if (opts.search) params.search = opts.search
  if (opts.ordering) params.ordering = opts.ordering
  api.get('invoices/', { params })
    .then((res) => {
      receipts.value = res.data.results ?? res.data ?? []
      totalCount.value = res.data.count ?? receipts.value.length
    })
    .catch(() => {
      receipts.value = []
      totalCount.value = 0
    })
    .finally(() => { loading.value = false })
}

async function openDetail(row) {
  try {
    const res = await api.get(`invoice/${row.id}/`)
    detailInvoice.value = res.data
  } catch {
    detailInvoice.value = row
  }
}

async function reprint(row) {
  try {
    const res = await api.get(`invoice/${row.id}/pdf/`, { responseType: 'blob' })
    const url = URL.createObjectURL(res.data)
    const w = window.open(url, '_blank')
    if (w) w.focus()
    else window.location.href = url
  } catch (e) {
    console.error(e)
    alert('PDF ထုတ်ယူခြင်း မအောင်မြင်ပါ။')
  }
}

onMounted(() => doFetch())
</script>
