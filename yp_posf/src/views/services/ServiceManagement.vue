<template>
  <div class="flex-1 p-4 md:p-6 lg:p-8 space-y-6 max-w-[1600px] mx-auto bg-[#f4f4f4] min-h-full">
    <h1 class="text-2xl md:text-3xl font-black tracking-tight text-[#1a1a1a]">စက်ပြင်ဝန်ဆောင်မှု</h1>

    <div class="bg-white p-4 md:p-6 rounded-2xl border border-[var(--color-border)] shadow-sm">
      <h2 class="text-lg font-bold text-[#1a1a1a] mb-4">စက်ပြင်လက်ခံလွှာ</h2>
      <ServiceEntryForm @saved="handleSaved" />
    </div>

    <div class="bg-white p-4 md:p-6 rounded-2xl border border-[var(--color-border)] shadow-sm">
      <RepairCalendar @select="handleSaved" />
    </div>

    <FilterDataTable
      ref="tableRef"
      light
      title="Repair List"
      :columns="columns"
      :data="repairs"
      :total-count="totalCount"
      :loading="loading"
      search-placeholder="Repair No, Item, Customer, Status ရှာပါ..."
      :default-page-size="20"
      empty-message="စက်ပြင်စာရင်း မရှိသေးပါ။"
      @fetch-data="fetchData"
    >
      <template #cell-repair_no="{ value }">
        <span class="font-mono font-bold text-[#1a1a1a] bg-[var(--color-bg-card)] px-2.5 py-1 rounded-lg border border-[var(--color-border)]">{{ value || '–' }}</span>
      </template>
      <template #cell-item_name="{ value }">
        <span class="font-semibold text-[#1a1a1a] text-fluid-sm">{{ value || '–' }}</span>
      </template>
      <template #cell-customer_display="{ row }">
        <span class="text-[#374151] text-fluid-sm">{{ row.customer_info?.name || row.customer_name || '–' }}</span>
      </template>
      <template #cell-status="{ value }">
        <span :class="statusClass(value)" class="px-3 py-1 rounded-lg text-[10px] font-bold uppercase border">
          {{ value }}
        </span>
      </template>
      <template #cell-received_date="{ value }">
        <span class="text-[#4b5563] text-fluid-sm">{{ value ? new Date(value).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : '–' }}</span>
      </template>
      <template #actions="{ row }">
        <button
          @click="openRepair(row)"
          class="btn-secondary px-3 py-1.5 rounded-xl text-fluid-sm font-bold text-amber-600 hover:text-amber-700 border border-[var(--color-border)] interactive"
        >
          VIEW
        </button>
      </template>
    </FilterDataTable>

    <div
      v-if="showInvoice && selectedRepair"
      class="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100] overflow-y-auto flex justify-center py-10 print:static print:block print:bg-transparent print:p-0"
      @click.self="showInvoice = false"
    >
      <div class="bg-white relative w-full max-w-[850px] p-4 md:p-6 rounded-2xl border border-[var(--color-border)] shadow-xl print:m-0 print:p-0 print:max-w-none">
        <button
          @click="showInvoice = false"
          class="absolute top-4 right-4 print:hidden btn-secondary px-4 py-2 rounded-xl font-bold text-fluid-sm z-[110] border border-[var(--surface-border)]"
        >
          ✕ CLOSE
        </button>
        <div class="p-2">
          <RepairInvoice :repair="selectedRepair" @updated="handleUpdate" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ServiceEntryForm from '@/components/ServiceEntry.vue'
import RepairCalendar from '@/components/RepairCalendar.vue'
import RepairInvoice from '@/components/RepairInvoice.vue'
import FilterDataTable from '@/components/FilterDataTable.vue'
import api from '@/services/api'

const tableRef = ref(null)
const repairs = ref([])
const totalCount = ref(0)
const loading = ref(false)
const showInvoice = ref(false)
const selectedRepair = ref(null)

const columns = [
  { key: 'repair_no', label: 'Repair No', sortable: true },
  { key: 'item_name', label: 'Item', sortable: true },
  { key: 'customer_display', label: 'Customer', sortable: false },
  { key: 'status', label: 'Status', sortable: true },
  { key: 'received_date', label: 'Received', sortable: true, type: 'date' },
]

function statusClass(s) {
  const st = (s || '').toLowerCase()
  if (st === 'ready' || st === 'completed') return 'bg-emerald-100 text-emerald-700 border-emerald-300'
  if (st === 'processing' || st === 'pending') return 'bg-amber-100 text-amber-700 border-amber-300'
  if (st === 'rejected' || st === 'cancelled') return 'bg-rose-100 text-rose-700 border-rose-300'
  return 'bg-[var(--color-bg-card)] text-[#4b5563] border-[var(--color-border)]'
}

function fetchData({ search, page, pageSize, ordering }) {
  loading.value = true
  const params = { page, page_size: pageSize }
  if (search) params.search = search
  if (ordering) params.ordering = ordering
  api
    .get('service/repairs/', { params })
    .then((res) => {
      const list = res.data.results ?? res.data ?? []
      repairs.value = list.map((r) => ({
        ...r,
        customer_name: r.customer_info?.name || r.customer_info?.phone_number || null,
      }))
      totalCount.value = res.data.count ?? repairs.value.length
    })
    .catch(() => {
      repairs.value = []
      totalCount.value = 0
    })
    .finally(() => {
      loading.value = false
    })
}

function handleSaved(data) {
  if (!data) return
  selectedRepair.value = data
  showInvoice.value = true
  tableRef.value?.emitFetch()
}

function handleUpdate(updatedData) {
  selectedRepair.value = updatedData
  tableRef.value?.emitFetch()
}

function openRepair(row) {
  selectedRepair.value = row
  showInvoice.value = true
}
</script>
