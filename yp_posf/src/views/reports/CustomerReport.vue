<template>
  <div class="flex-1 p-4 md:p-6 space-y-6 max-w-[1600px] mx-auto bg-[#f4f4f4] min-h-full">
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-black tracking-tight text-[#1a1a1a]">ဝယ်ယူသူ စာရင်း</h1>
        <p class="text-xs font-bold text-[#6b7280] uppercase tracking-wider mt-1">Customer Report</p>
      </div>
      <button
        @click="tableRef?.emitFetch()"
        :disabled="loading"
        class="px-4 py-2.5 rounded-xl bg-amber-500 text-white font-bold text-sm hover:bg-amber-600 transition-all disabled:opacity-70 flex items-center gap-2"
      >
        <RefreshCw :class="{ 'animate-spin': loading }" class="w-4 h-4" />
        Refresh
      </button>
    </div>

    <FilterDataTable
      ref="tableRef"
      light
      :columns="columns"
      :data="customers"
      :total-count="totalCount"
      :loading="loading"
      title="Customers"
      search-placeholder="အမည်၊ ဖုန်းနံပါတ် ရှာပါ..."
      :default-page-size="20"
      empty-message="ဝယ်ယူသူ စာရင်းမရှိသေးပါ။"
      @fetch-data="fetchData"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import FilterDataTable from '@/components/FilterDataTable.vue'
import { RefreshCw } from 'lucide-vue-next'
import api from '@/services/api'

const tableRef = ref(null)
const customers = ref([])
const totalCount = ref(0)
const loading = ref(false)

const columns = [
  { key: 'name', label: 'အမည်', sortable: true },
  { key: 'phone_number', label: 'ဖုန်းနံပါတ်', sortable: true },
  { key: 'email', label: 'အီးမေးလ်', sortable: true },
  { key: 'preferred_branch_name', label: 'ကြိုက်နှစ်သက်သော ဆိုင်', sortable: true },
]

function fetchData({ search, page, pageSize, ordering }) {
  loading.value = true
  const params = { page, page_size: pageSize }
  if (search) params.search = search
  if (ordering) params.ordering = ordering
  api
    .get('customers/', { params })
    .then((res) => {
      customers.value = res.data.results ?? res.data ?? []
      totalCount.value = res.data.count ?? customers.value.length
    })
    .catch(() => {
      customers.value = []
      totalCount.value = 0
    })
    .finally(() => {
      loading.value = false
    })
}
</script>
