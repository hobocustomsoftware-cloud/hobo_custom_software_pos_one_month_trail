<template>
  <div class="w-full max-w-6xl mx-auto px-2 sm:px-4 space-y-4">
    <h1 class="text-lg sm:text-xl font-semibold text-[var(--color-fg)]">Shift</h1>
    <p class="text-sm text-[var(--color-fg-muted)]">Shift-based sales summary.</p>

    <div class="flex flex-wrap items-center gap-4 mb-4">
      <div class="flex items-center gap-2">
        <label class="text-sm text-[var(--color-fg-muted)]">From</label>
        <input v-model="dateFrom" type="date" class="glass-input px-3 py-2 rounded-lg text-sm" />
      </div>
      <div class="flex items-center gap-2">
        <label class="text-sm text-[var(--color-fg-muted)]">To</label>
        <input v-model="dateTo" type="date" class="glass-input px-3 py-2 rounded-lg text-sm" />
      </div>
      <button type="button" @click="fetchShifts" class="btn-primary px-4 py-2 text-sm">Apply</button>
    </div>

    <div class="bg-white rounded-xl shadow-sm overflow-hidden min-h-[min(400px,55vh)]">
      <div v-if="loading" class="p-8 text-center text-[var(--color-fg-muted)]">Loading...</div>
      <div v-else-if="shiftRows.length === 0" class="p-12 text-center text-[var(--color-fg-muted)]">
        ရွေးထားသော ရက်စွဲအတွင်း အရောင်းစာရင်း မရှိပါ။
      </div>
      <div v-else class="overflow-x-auto">
        <table class="w-full min-w-[400px]">
          <thead class="bg-[var(--color-bg-light)]">
            <tr>
              <th class="p-3 text-left text-sm font-semibold text-[var(--color-fg)]">Date</th>
              <th class="p-3 text-right text-sm font-semibold text-[var(--color-fg)]">Invoices</th>
              <th class="p-3 text-right text-sm font-semibold text-[var(--color-fg)]">Total (MMK)</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[var(--color-border)]">
            <tr v-for="row in shiftRows" :key="row.date" class="hover:bg-[var(--color-bg-light)]">
              <td class="p-3 font-medium">{{ row.date }}</td>
              <td class="p-3 text-right">{{ row.count }}</td>
              <td class="p-3 text-right font-medium">{{ row.total.toLocaleString(undefined, { maximumFractionDigits: 0 }) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

const dateFrom = ref('')
const dateTo = ref('')
const shiftRows = ref([])
const loading = ref(false)

function toDateStr(d) {
  return new Date(d).toISOString().slice(0, 10)
}

async function fetchShifts() {
  loading.value = true
  shiftRows.value = []
  try {
    const params = { page_size: 500 }
    const res = await api.get('invoices/', { params })
    const list = res.data.results ?? res.data ?? []
    const from = dateFrom.value ? new Date(dateFrom.value) : null
    const to = dateTo.value ? new Date(dateTo.value) : null
    const byDate = {}
    for (const inv of list) {
      const d = inv.created_at ? toDateStr(inv.created_at) : ''
      if (!d) continue
      if (from && new Date(d) < from) continue
      if (to && new Date(d) > to) continue
      if (!byDate[d]) byDate[d] = { date: d, count: 0, total: 0 }
      byDate[d].count += 1
      byDate[d].total += Number(inv.total_amount) || 0
    }
    shiftRows.value = Object.values(byDate).sort((a, b) => b.date.localeCompare(a.date))
  } catch {
    shiftRows.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  const t = new Date()
  dateTo.value = toDateStr(t)
  const f = new Date(t)
  f.setDate(f.getDate() - 7)
  dateFrom.value = toDateStr(f)
  fetchShifts()
})
</script>
