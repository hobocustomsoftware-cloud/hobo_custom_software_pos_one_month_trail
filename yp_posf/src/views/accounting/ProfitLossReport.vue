<template>
  <div class="layout-container space-y-6 max-w-[1600px] mx-auto bg-[#f4f4f4] min-h-full" style="gap: var(--fluid-gap);">
    <div class="flex flex-wrap justify-between items-center" style="gap: var(--fluid-gap);">
      <div>
        <h1 class="text-fluid-xl font-black uppercase tracking-tight text-[#1a1a1a]">P&L အစီရင်ခံစာ</h1>
        <p class="text-fluid-sm font-medium text-[#6b7280] uppercase tracking-wider mt-1">Profit & Loss Report</p>
      </div>
      <button
        @click="fetchData"
        :disabled="loading"
        class="btn-primary px-4 py-2.5 flex items-center gap-2 interactive disabled:opacity-70"
      >
        <RefreshCw :class="{ 'animate-spin': loading }" class="w-4 h-4" />
        Refresh
      </button>
    </div>

    <!-- Date Range Filter -->
    <div class="bg-white rounded-xl border border-[var(--color-border)] shadow-sm p-5 flex flex-wrap" style="gap: var(--fluid-gap);">
      <div class="flex-1 min-w-[200px]">
        <label class="block mb-2 text-sm font-medium text-[#374151]">စတင်ရက်</label>
        <input
          v-model="filters.startDate"
          type="date"
          class="glass-input w-full px-4 py-2"
          @change="fetchData"
        />
      </div>
      <div class="flex-1 min-w-[200px]">
        <label class="block mb-2 text-sm font-medium text-[#374151]">ပြီးဆုံးရက်</label>
        <input
          v-model="filters.endDate"
          type="date"
          class="glass-input w-full px-4 py-2"
          @change="fetchData"
        />
      </div>
    </div>

    <!-- P&L Summary Cards -->
    <div v-if="pnlSummary" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4" style="gap: var(--fluid-gap);">
      <div class="bg-white rounded-xl border border-[var(--color-border)] shadow-sm p-5 interactive">
        <div class="text-sm font-medium text-[#6b7280] mb-2">စုစုပေါင်း ဝင်ငွေ</div>
        <div class="text-fluid-xl font-black text-emerald-600">{{ formatCurrency(pnlSummary.total_income) }}</div>
      </div>
      <div class="bg-white rounded-xl border border-[var(--color-border)] shadow-sm p-5 interactive">
        <div class="text-sm font-medium text-[#6b7280] mb-2">စုစုပေါင်း ကုန်ကျစရိတ်</div>
        <div class="text-fluid-xl font-black text-rose-600">{{ formatCurrency(pnlSummary.total_expenses) }}</div>
      </div>
      <div class="bg-white rounded-xl border border-[var(--color-border)] shadow-sm p-5 interactive">
        <div class="text-sm font-medium text-[#6b7280] mb-2">အမြတ်အစွန်း</div>
        <div class="text-fluid-xl font-black" :class="pnlSummary.net_profit >= 0 ? 'text-emerald-600' : 'text-rose-600'">
          {{ formatCurrency(pnlSummary.net_profit) }}
        </div>
      </div>
      <div class="bg-white rounded-xl border border-[var(--color-border)] shadow-sm p-5 interactive">
        <div class="text-sm font-medium text-[#6b7280] mb-2">အမြတ်အစွန်း %</div>
        <div class="text-fluid-xl font-black" :class="(Number(pnlSummary.profit_margin_percent) ?? 0) >= 0 ? 'text-emerald-600' : 'text-rose-600'">
          {{ formatPct(pnlSummary.profit_margin_percent) }}%
        </div>
      </div>
    </div>

    <!-- Profit from Sales (Gross Profit) -->
    <div v-if="profitFromSales" class="bg-white rounded-xl border border-[var(--color-border)] shadow-sm p-6">
      <h2 class="text-lg font-bold text-[#1a1a1a] mb-4">ရောင်းချမှု အမြတ်အစွန်း (Gross Profit)</h2>
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
          <div class="text-[#6b7280] text-xs font-bold uppercase mb-1">ရောင်းရငွေ</div>
          <div class="text-xl font-black text-emerald-600">{{ formatCurrency(profitFromSales.total_revenue) }}</div>
        </div>
        <div>
          <div class="text-[#6b7280] text-xs font-bold uppercase mb-1">ကုန်ကျစရိတ်</div>
          <div class="text-xl font-black text-rose-600">{{ formatCurrency(profitFromSales.total_cost) }}</div>
        </div>
        <div>
          <div class="text-[#6b7280] text-xs font-bold uppercase mb-1">အမြတ်အစွန်း</div>
          <div class="text-xl font-black text-emerald-600">{{ formatCurrency(profitFromSales.gross_profit) }}</div>
        </div>
        <div>
          <div class="text-[#6b7280] text-xs font-bold uppercase mb-1">အမြတ်အစွန်း %</div>
          <div class="text-xl font-black text-emerald-600">{{ formatPct(profitFromSales.gross_profit_margin_percent) }}%</div>
        </div>
      </div>
    </div>

    <!-- Profit Margin Analysis -->
    <div v-if="marginAnalysis" class="bg-white rounded-xl border border-[var(--color-border)] shadow-sm p-6">
      <h2 class="text-lg font-bold text-[#1a1a1a] mb-4">အမြတ်အစွန်း ခွဲခြမ်းစိတ်ဖြာမှု</h2>
      <div class="space-y-3">
        <div class="flex justify-between items-center p-3 bg-[var(--color-bg-card)] rounded-lg">
          <span class="text-[#4b5563] text-sm">လက်ရှိ အမြတ်အစွန်း %</span>
          <span class="text-[#1a1a1a] font-bold">{{ formatPct(marginAnalysis.current_margin) }}%</span>
        </div>
        <div class="flex justify-between items-center p-3 bg-[var(--color-bg-card)] rounded-lg">
          <span class="text-[#4b5563] text-sm">ယခင်ကာလ အမြတ်အစွန်း %</span>
          <span class="text-[#1a1a1a] font-bold">{{ formatPct(marginAnalysis.previous_margin) }}%</span>
        </div>
        <div class="flex justify-between items-center p-3 bg-[var(--color-bg-card)] rounded-lg">
          <span class="text-[#4b5563] text-sm">ပြောင်းလဲမှု</span>
          <span class="font-bold" :class="(Number(marginAnalysis.margin_change) ?? 0) >= 0 ? 'text-emerald-600' : 'text-rose-600'">
            {{ (Number(marginAnalysis.margin_change) ?? 0) >= 0 ? '+' : '' }}{{ formatPct(marginAnalysis.margin_change) }}%
          </span>
        </div>
        <div class="flex justify-between items-center p-3 bg-[var(--color-bg-card)] rounded-lg">
          <span class="text-[#4b5563] text-sm">ဒေါ်လာဈေး ပြောင်းလဲမှု</span>
          <span class="font-bold" :class="(Number(marginAnalysis.usd_rate_change_percent) ?? 0) >= 0 ? 'text-rose-600' : 'text-emerald-600'">
            {{ (Number(marginAnalysis.usd_rate_change_percent) ?? 0) >= 0 ? '+' : '' }}{{ formatPct(marginAnalysis.usd_rate_change_percent) }}%
          </span>
        </div>
        <div v-if="marginAnalysis.suggestion" class="p-4 bg-amber-100 border border-amber-300 rounded-lg">
          <div class="text-amber-800 text-sm font-bold mb-1">💡 အကြံပြုချက်</div>
          <div class="text-[#374151] text-sm">{{ marginAnalysis.suggestion }}</div>
        </div>
      </div>
    </div>

    <!-- Transactions List -->
    <div class="bg-white rounded-xl border border-[var(--color-border)] shadow-sm overflow-hidden">
      <h2 class="text-fluid-lg font-bold text-[#1a1a1a] p-5 border-b border-[var(--color-border)]">Transactions</h2>
      <div class="overflow-x-auto custom-scrollbar">
        <table class="w-full">
          <thead class="bg-[var(--color-bg-card)] border-b border-[var(--color-border)]">
            <tr>
              <th class="p-4 text-left text-xs font-bold text-[#6b7280] uppercase">ရက်စွဲ</th>
              <th class="p-4 text-left text-xs font-bold text-[#6b7280] uppercase">အမျိုးအစား</th>
              <th class="p-4 text-left text-xs font-bold text-[#6b7280] uppercase">ဖော်ပြချက်</th>
              <th class="p-4 text-right text-xs font-bold text-[#6b7280] uppercase">ငွေပမာဏ</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[var(--color-border)]">
            <tr v-if="loading" class="text-center">
              <td colspan="4" class="p-8 text-[#6b7280]">Loading...</td>
            </tr>
            <tr v-else-if="transactions.length === 0" class="text-center">
              <td colspan="4" class="p-8 text-[#6b7280]">Transaction မရှိပါ။</td>
            </tr>
            <tr v-else v-for="tx in transactions" :key="tx.id" class="interactive hover:bg-[var(--color-bg-card)]">
              <td class="p-4 text-[#1a1a1a] text-fluid-sm">{{ formatDate(tx.transaction_date) }}</td>
              <td class="p-4">
                <span
                  :class="tx.transaction_type === 'income' ? 'bg-emerald-100 text-emerald-700 border border-emerald-300' : 'bg-rose-100 text-rose-700 border border-rose-300'"
                  class="px-3 py-1.5 rounded-lg text-fluid-sm font-semibold uppercase"
                >
                  {{ tx.transaction_type === 'income' ? 'ဝင်ငွေ' : 'ကုန်ကျစရိတ်' }}
                </span>
              </td>
              <td class="p-4 text-[#1a1a1a] text-fluid-sm">
                {{ tx.transaction_type === 'income' ? (tx.sale_invoice || '-') : (tx.expense_description || '-') }}
              </td>
              <td class="p-4 text-right font-bold text-fluid-base" :class="tx.amount >= 0 ? 'text-emerald-600' : 'text-rose-600'">
                {{ formatCurrency(tx.amount) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { RefreshCw } from 'lucide-vue-next'
import api from '@/services/api'

const pnlSummary = ref(null)
const profitFromSales = ref(null)
const marginAnalysis = ref(null)
const transactions = ref([])
const loading = ref(false)

const filters = ref({
  startDate: new Date(new Date().setDate(new Date().getDate() - 30)).toISOString().split('T')[0],
  endDate: new Date().toISOString().split('T')[0],
})

const fetchData = async () => {
  loading.value = true
  try {
    const token = localStorage.getItem('access_token')
    const params = {}
    if (filters.value.startDate) params.start_date = filters.value.startDate
    if (filters.value.endDate) params.end_date = filters.value.endDate

    // Fetch all data in parallel
    // api service က auto token injection လုပ်ပေးတယ်
    const [pnlRes, profitRes, marginRes, txRes] = await Promise.all([
      api.get('accounting/pnl/summary/', { params }),
      api.get('accounting/pnl/profit-from-sales/', { params }),
      api.get('accounting/pnl/margin-analysis/'),
      api.get('accounting/transactions/', { params }),
    ])

    pnlSummary.value = pnlRes.data
    profitFromSales.value = profitRes.data
    marginAnalysis.value = marginRes.data
    transactions.value = txRes.data.results ?? txRes.data ?? []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('my-MM', { year: 'numeric', month: 'short', day: 'numeric' })
}

const formatCurrency = (amount) => {
  if (!amount && amount !== 0) return '0 MMK'
  const num = Number(amount)
  return (num >= 0 ? '+' : '') + Math.round(Number(num) || 0).toLocaleString('my-MM', { maximumFractionDigits: 0, minimumFractionDigits: 0 }) + ' MMK'
}

const formatPct = (value) => {
  const n = Number(value)
  return (Number.isFinite(n) ? n : 0).toFixed(2)
}

let saleCompletedListener = null
onMounted(() => {
  fetchData()
  saleCompletedListener = () => fetchData()
  window.addEventListener('sale-completed', saleCompletedListener)
})
onBeforeUnmount(() => {
  if (saleCompletedListener) window.removeEventListener('sale-completed', saleCompletedListener)
})
</script>
