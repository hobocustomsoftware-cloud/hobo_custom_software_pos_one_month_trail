<template>
  <div class="flex-1 p-4 md:p-6 space-y-6 max-w-[1600px] mx-auto font-sans">
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-black tracking-tight text-[var(--color-fg)]">ပစ္စည်းစာရင်း အစီရင်ခံစာ</h1>
        <p class="text-sm font-medium text-[var(--color-fg-muted)] uppercase tracking-wider mt-1">Stock Analysis</p>
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
      :data="products"
      :columns="columns"
      title="Product Inventory"
      search-placeholder="SKU, Name, Category ရှာပါ..."
      :items-per-page="15"
      :search-keys="['sku', 'name', 'category_name']"
      empty-message="ပစ္စည်းစာရင်း မရှိသေးပါ။"
    >
      <template #cell-retail_price="{ value }">
        <span class="font-bold text-[var(--color-fg)]">{{ value != null ? Math.round(Number(value)).toLocaleString(undefined, { maximumFractionDigits: 0 }) + ' MMK' : '-' }}</span>
      </template>
      <template #cell-shop_stock="{ value, row }">
        <span :class="stockClass(value, row)">
          {{ value ?? row.total_stock ?? 0 }}
        </span>
      </template>
    </DataTable>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import DataTable from '@/components/DataTable.vue'
import { RefreshCw } from 'lucide-vue-next'
import api from '@/services/api'

const products = ref([])
const loading = ref(false)

const columns = [
  { key: 'sku', label: 'SKU', sortable: true },
  { key: 'name', label: 'Product Name', sortable: true },
  { key: 'category_name', label: 'Category', sortable: true },
  { key: 'shop_stock', label: 'Stock', sortable: true, type: 'number' },
  { key: 'retail_price', label: 'Price', sortable: true, type: 'currency' },
]

const stockClass = (val, row) => {
  const qty = val ?? row?.total_stock ?? 0
  return qty <= 0 ? 'text-rose-600 font-bold' : 'text-[var(--color-fg)]'
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await api.get('staff/items/')
    products.value = Array.isArray(res.data) ? res.data : (res.data?.results ?? [])
  } catch (e) {
    console.error(e)
    products.value = []
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>
