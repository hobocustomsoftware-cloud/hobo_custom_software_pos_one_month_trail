<template>
  <div class="bg-white p-5 rounded-2xl border border-[var(--color-border)] shadow-sm">
    <div class="flex items-center justify-between mb-4">
      <div>
        <h3 class="text-lg font-bold text-[var(--color-fg)] flex items-center gap-2">
          <span class="text-2xl">🔮</span>
          <span>Stock Predictions</span>
        </h3>
        <p class="text-xs text-[var(--color-fg-muted)] mt-1">ပစ္စည်းလက်ကျန် နှင့် နေ့စဉ်ပျမ်းမျှ ရောင်းအားအရ ကုန်ဆုံးမည့်ရက် ခန့်မှန်းချက်။ Duplicate များ ဖြုတ်ပြီး ပြသထားသည်။</p>
      </div>
      <button
        @click="refresh"
        :disabled="loading"
        class="text-[var(--color-fg-muted)] hover:text-[var(--color-fg)] transition-colors disabled:opacity-50"
      >
        {{ loading ? '⏳' : '🔄' }}
      </button>
    </div>

    <div v-if="loading" class="text-center py-8 text-[var(--color-fg-muted)]">
      Analyzing stock movements...
    </div>

    <div v-else-if="paginatedPredictions.length > 0" class="space-y-3">
      <div
        v-for="(pred, idx) in paginatedPredictions"
        :key="idx"
        class="p-4 rounded-xl border bg-[var(--color-bg-light)]"
        :class="{
          'border-red-300': pred.status === 'out_of_stock',
          'border-amber-300': pred.status === 'low_stock',
          'border-[var(--color-border)]': pred.status === 'normal',
        }"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1 min-w-0">
            <h4 class="font-bold text-[var(--color-fg)] mb-1 truncate">{{ pred.product_name }}</h4>
            <div class="flex items-center gap-2 mb-2 flex-wrap">
              <span
                class="px-2 py-1 rounded text-xs font-bold"
                :class="{
                  'bg-red-100 text-red-700': pred.status === 'out_of_stock',
                  'bg-amber-100 text-amber-700': pred.status === 'low_stock',
                  'bg-emerald-100 text-emerald-700': pred.status === 'normal',
                }"
              >
                {{ pred.status === 'out_of_stock' ? 'Out of Stock' : pred.status === 'low_stock' ? 'Low Stock' : 'Normal' }}
              </span>
              <span class="text-xs text-[var(--color-fg-muted)]">Confidence: {{ pred.confidence }}</span>
            </div>
            <div class="space-y-1 text-sm text-[var(--color-fg)]">
              <div class="flex justify-between gap-2">
                <span class="text-[var(--color-fg-muted)] shrink-0">Current Stock:</span>
                <span class="font-bold">{{ pred.current_stock }}</span>
              </div>
              <div class="flex justify-between gap-2">
                <span class="text-[var(--color-fg-muted)] shrink-0">Daily Avg Consumption:</span>
                <span class="font-bold">{{ pred.daily_avg_consumption }}</span>
              </div>
              <div v-if="pred.predicted_out_of_stock_date" class="flex justify-between gap-2">
                <span class="text-[var(--color-fg-muted)] shrink-0">Predicted Out of Stock:</span>
                <span
                  class="font-bold"
                  :class="pred.days_until_out_of_stock <= 7 ? 'text-red-600' : 'text-[var(--color-fg)]'"
                >
                  {{ pred.predicted_out_of_stock_date }}
                  <span class="text-xs ml-1">({{ pred.days_until_out_of_stock }} days)</span>
                </span>
              </div>
              <div v-else class="flex justify-between gap-2">
                <span class="text-[var(--color-fg-muted)]">Status:</span>
                <span class="font-bold text-red-600">Already Out of Stock</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="text-center py-8 text-[var(--color-fg-muted)]">
      No predictions available. Need more movement data.
    </div>

    <!-- Paginator -->
    <div v-if="predictions.length > pageSize" class="mt-4 flex items-center justify-between border-t border-[var(--color-border)] pt-3">
      <span class="text-xs text-[var(--color-fg-muted)]">
        {{ (currentPage - 1) * pageSize + 1 }}-{{ Math.min(currentPage * pageSize, predictions.length) }} of {{ predictions.length }}
      </span>
      <div class="flex gap-2">
        <button
          :disabled="currentPage <= 1"
          @click="currentPage--"
          class="px-3 py-1 rounded-lg border border-[var(--color-border)] bg-white text-[var(--color-fg)] hover:bg-[var(--color-bg-light)] disabled:opacity-40 text-sm font-bold"
        >
          Prev
        </button>
        <button
          :disabled="currentPage >= totalPages"
          @click="currentPage++"
          class="px-3 py-1 rounded-lg border border-[var(--color-border)] bg-white text-[var(--color-fg)] hover:bg-[var(--color-bg-light)] disabled:opacity-40 text-sm font-bold"
        >
          Next
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'

const PAGE_SIZE = 10
const predictions = ref([])
const loading = ref(false)
const currentPage = ref(1)

const totalPages = computed(() => Math.max(1, Math.ceil(predictions.value.length / PAGE_SIZE)))
const paginatedPredictions = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  return predictions.value.slice(start, start + PAGE_SIZE)
})
const pageSize = PAGE_SIZE

const fetchPredictions = async () => {
  loading.value = true
  try {
    const res = await api.get('ai/stock-prediction/', { params: { limit: 50, offset: 0 } })
    const raw = res.data.predictions || []
    const seen = new Set()
    predictions.value = raw.filter((p) => {
      const key = p.product_id ?? p.product_name ?? p.id ?? JSON.stringify(p)
      if (seen.has(key)) return false
      seen.add(key)
      return true
    })
    currentPage.value = 1
  } catch (err) {
    console.error('Failed to fetch stock predictions:', err)
    predictions.value = []
  } finally {
    loading.value = false
  }
}

const refresh = () => {
  fetchPredictions()
}

onMounted(() => {
  fetchPredictions()
})
</script>

