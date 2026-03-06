<template>
  <div class="layout-container space-y-6 bg-[#f4f4f4] min-h-full" style="gap: var(--fluid-gap);">
    <h1 class="text-fluid-xl font-black uppercase tracking-tight text-[#1a1a1a]">တပ်ဆင်မှု Dashboard</h1>

    <!-- Statistics -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5" style="gap: var(--fluid-gap);">
      <div class="bg-white rounded-xl border border-[var(--color-border)] shadow-sm p-5 interactive">
        <div class="text-sm font-medium text-[#6b7280] mb-2">Total Active</div>
        <div class="text-fluid-xl font-black text-[#1a1a1a]">{{ statistics.total_active || 0 }}</div>
      </div>
      <div class="bg-white rounded-xl border border-[var(--color-border)] shadow-sm p-5 interactive">
        <div class="text-sm font-medium text-yellow-700 mb-2">Pending</div>
        <div class="text-fluid-xl font-black text-yellow-600">{{ statistics.pending || 0 }}</div>
      </div>
      <div class="bg-white rounded-xl border border-[var(--color-border)] shadow-sm p-5 interactive">
        <div class="text-sm font-medium text-amber-700 mb-2">သွားတိုင်းရမည်</div>
        <div class="text-fluid-xl font-black text-amber-600">{{ statistics.site_visit || 0 }}</div>
      </div>
      <div class="bg-white rounded-xl border border-[var(--color-border)] shadow-sm p-5 interactive">
        <div class="text-sm font-medium text-blue-700 mb-2">In Progress</div>
        <div class="text-fluid-xl font-black text-blue-600">{{ statistics.in_progress || 0 }}</div>
      </div>
      <div class="bg-white rounded-xl border border-[var(--color-border)] shadow-sm p-5 interactive">
        <div class="text-sm font-medium text-green-700 mb-2">Completed</div>
        <div class="text-fluid-xl font-black text-green-600">{{ statistics.completed || 0 }}</div>
      </div>
    </div>

    <!-- Active Installations List -->
    <div class="bg-white rounded-xl border border-[var(--color-border)] shadow-sm overflow-hidden">
      <div class="p-5 border-b border-[var(--color-border)]">
        <h2 class="text-fluid-lg font-bold text-[#1a1a1a]">Active Installation Jobs</h2>
      </div>
      
      <div v-if="loading" class="p-8 text-center text-[#4b5563]">Loading...</div>
      <div v-else-if="installations.length === 0" class="p-8 text-center text-[#4b5563]">
        Active installation မရှိပါ။
      </div>
      <div v-else class="overflow-x-auto custom-scrollbar">
        <table class="w-full">
          <thead class="bg-[var(--color-bg-card)] border-b border-[var(--color-border)]">
            <tr>
              <th class="p-4 text-left text-xs font-bold text-[#6b7280] uppercase">Installation No.</th>
              <th class="p-4 text-left text-xs font-bold text-[#6b7280] uppercase">Invoice</th>
              <th class="p-4 text-left text-xs font-bold text-[#6b7280] uppercase">Customer</th>
              <th class="p-4 text-left text-xs font-bold text-[#6b7280] uppercase">Address</th>
              <th class="p-4 text-left text-xs font-bold text-[#6b7280] uppercase">Date</th>
              <th class="p-4 text-left text-xs font-bold text-[#6b7280] uppercase">Technician</th>
              <th class="p-4 text-left text-xs font-bold text-[#6b7280] uppercase">Status</th>
              <th class="p-4 text-left text-xs font-bold text-[#6b7280] uppercase">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[var(--color-border)]">
            <tr v-for="inst in installations" :key="inst.id" class="interactive hover:bg-[var(--color-bg-card)]">
              <td class="p-4 font-mono text-[#1a1a1a]">{{ inst.installation_no }}</td>
              <td class="p-4 text-[#374151]">{{ inst.invoice_number }}</td>
              <td class="p-4">
                <div class="text-[#1a1a1a] font-medium">{{ inst.customer_name }}</div>
                <div class="text-fluid-sm text-[#6b7280]">{{ inst.customer_phone }}</div>
              </td>
              <td class="p-4 text-[#374151] text-fluid-sm">{{ inst.installation_address }}</td>
              <td class="p-4 text-[#374151]">{{ formatDate(inst.installation_date) }}</td>
              <td class="p-4 text-[#374151]">{{ inst.technician_name || '—' }}</td>
              <td class="p-4">
                <span :class="getStatusClass(inst.status)" class="px-3 py-1.5 rounded-lg text-fluid-sm font-semibold">
                  {{ getStatusText(inst.status) }}
                </span>
              </td>
              <td class="p-4">
                <RouterLink
                  :to="`/installation/${inst.id}`"
                  class="btn-secondary px-4 py-2 text-fluid-sm inline-block"
                >
                  View
                </RouterLink>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import api from '@/services/api'

const installations = ref([])
const statistics = ref({})
const loading = ref(false)

const fetchDashboard = async () => {
  loading.value = true
  try {
    // api service က auto token injection လုပ်ပေးတယ်
    const res = await api.get('installation/dashboard/')
    installations.value = res.data.installations || []
    statistics.value = res.data.statistics || {}
  } catch (error) {
    console.error(error)
    alert('Dashboard data ရယူရာတွင် error ဖြစ်ပါသည်။')
  } finally {
    loading.value = false
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('my-MM')
}

const getStatusClass = (status) => {
  const classes = {
    pending: 'bg-yellow-500/20 text-yellow-300 border border-yellow-400/30',
    site_visit: 'bg-amber-500/20 text-amber-300 border border-amber-400/30',
    in_progress: 'bg-blue-500/20 text-blue-300 border border-blue-400/30',
    completed: 'bg-green-500/20 text-green-300 border border-green-400/30',
    signed_off: 'bg-purple-500/20 text-purple-300 border border-purple-400/30',
    cancelled: 'bg-red-500/20 text-red-300 border border-red-400/30',
  }
  return classes[status] || 'bg-gray-500/20 text-gray-300 border border-gray-400/30'
}

const getStatusText = (status) => {
  const texts = {
    pending: 'Pending',
    site_visit: 'သွားတိုင်းရမည်',
    in_progress: 'In Progress',
    completed: 'Completed',
    signed_off: 'Signed Off',
    cancelled: 'Cancelled',
  }
  return texts[status] || status
}

onMounted(() => {
  fetchDashboard()
})
</script>
