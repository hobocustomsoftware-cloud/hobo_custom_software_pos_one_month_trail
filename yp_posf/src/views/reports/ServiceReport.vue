<template>
  <div class="flex-1 p-4 md:p-6 space-y-6 max-w-[1600px] mx-auto">
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-black tracking-tight text-slate-900">စက်ပြင်ဝန်ဆောင်မှု အစီရင်ခံစာ</h1>
        <p class="text-xs font-bold text-slate-500 uppercase tracking-wider mt-1">Repair Service Analysis</p>
      </div>
      <button
        @click="fetchData"
        :disabled="loading"
        class="px-4 py-2.5 rounded-xl bg-amber-500 text-white font-bold text-sm hover:bg-amber-600 transition-all disabled:opacity-70 flex items-center gap-2"
      >
        <RefreshCw :class="{ 'animate-spin': loading }" class="w-4 h-4" />
        Refresh
      </button>
    </div>

    <DataTable
      :data="repairs"
      :columns="columns"
      title="Repair Services"
      search-placeholder="Repair No, Item, Customer, Status ရှာပါ..."
      :items-per-page="15"
      :search-keys="['repair_no', 'item_name', 'status']"
      empty-message="စက်ပြင်ဝန်ဆောင်မှု မရှိသေးပါ။"
    >
      <template #cell-repair_no="{ value }">
        <span class="font-mono font-bold text-amber-700 bg-amber-50 px-2.5 py-1 rounded-lg">{{ value || '-' }}</span>
      </template>
      <template #cell-total_estimated_cost="{ value }">
        <span class="font-bold text-slate-800">{{ value != null ? Math.round(Number(value)).toLocaleString(undefined, { maximumFractionDigits: 0 }) + ' MMK' : '-' }}</span>
      </template>
      <template #cell-status="{ value }">
        <span :class="statusClass(value)" class="px-3 py-1 rounded-full text-xs font-bold uppercase">{{ value }}</span>
      </template>
      <template #cell-received_date="{ value }">
        {{ value ? new Date(value).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : '-' }}
      </template>
    </DataTable>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import DataTable from '@/components/DataTable.vue'
import { RefreshCw } from 'lucide-vue-next'
import api from '@/services/api'

const repairs = ref([])
const loading = ref(false)

const columns = [
  { key: 'repair_no', label: 'Repair No', sortable: true },
  { key: 'item_name', label: 'Item', sortable: true },
  { key: 'customer_info', label: 'Customer', sortable: false },
  { key: 'status', label: 'Status', sortable: true },
  { key: 'received_date', label: 'Received', sortable: true, type: 'date' },
  { key: 'total_estimated_cost', label: 'Est. Cost', sortable: true, type: 'currency' },
]

const statusClass = (s) => {
  const st = (s || '').toLowerCase()
  if (st === 'ready' || st === 'completed') return 'bg-emerald-100 text-emerald-700'
  if (st === 'processing' || st === 'pending') return 'bg-amber-100 text-amber-700'
  if (st === 'rejected' || st === 'cancelled') return 'bg-rose-100 text-rose-700'
  return 'bg-slate-100 text-slate-600'
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await api.get('service/repairs/')
    const list = res.data.results ?? res.data ?? []
    repairs.value = list.map((r) => ({
      ...r,
      customer_info: r.customer_info?.name || r.customer_name || '-',
    }))
  } catch (e) {
    console.error(e)
    repairs.value = []
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>
