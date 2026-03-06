<template>
  <div class="dashboard-card p-4 min-w-0 overflow-hidden">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-bold text-[var(--color-fg)] flex items-center gap-2">
        <span class="text-2xl">📊</span>
        <span>Business Insights</span>
      </h3>
      <button
        @click="refresh"
        :disabled="loading"
        class="text-[var(--color-fg-muted)] hover:text-[var(--color-fg)] transition-colors disabled:opacity-50"
      >
        {{ loading ? '⏳' : '🔄' }}
      </button>
    </div>

    <div v-if="loading" class="text-center py-8 text-[var(--color-fg-muted)]">
      Analyzing exchange rate trends...
    </div>

    <div v-else-if="insights.length > 0" class="space-y-4">
      <div
        v-for="(insight, idx) in insights"
        :key="idx"
        class="bg-[var(--color-bg-light)] p-4 rounded-xl border border-[var(--color-border)]"
      >
        <div class="flex items-center justify-between mb-3">
          <div>
            <h4 class="font-bold text-[var(--color-fg)]">Exchange Rate Analysis</h4>
            <p class="text-sm text-[var(--color-fg-muted)]">
              {{ insight.days_analyzed }} days analyzed
            </p>
          </div>
          <div class="text-right">
            <div class="text-2xl font-bold" :class="insight.trend === 'increasing' ? 'text-red-600' : 'text-emerald-600'">
              {{ insight.rate_change_percent > 0 ? '+' : '' }}{{ insight.rate_change_percent }}%
            </div>
            <div class="text-xs text-[var(--color-fg-muted)]">{{ insight.trend }}</div>
          </div>
        </div>

        <div class="space-y-2">
          <div class="flex justify-between text-sm">
            <span class="text-[var(--color-fg-muted)]">Current Rate:</span>
            <span class="font-bold text-[var(--color-fg)]">{{ Math.round(Number(insight.current_rate) || 0).toLocaleString(undefined, { maximumFractionDigits: 0 }) }} MMK/USD</span>
          </div>
          <div class="flex justify-between text-sm">
            <span class="text-[var(--color-fg-muted)]">Average Rate:</span>
            <span class="font-bold text-[var(--color-fg)]">{{ Math.round(Number(insight.average_rate) || 0).toLocaleString(undefined, { maximumFractionDigits: 0 }) }} MMK/USD</span>
          </div>
        </div>

        <div v-if="insight.recommendations && insight.recommendations.length > 0" class="mt-4 pt-4 border-t border-[var(--color-border)]">
          <h5 class="font-bold text-[var(--color-fg)] mb-2 text-sm">
            Price Adjustment Recommendations ({{ insight.recommendations.length }})
          </h5>
          <div class="space-y-2 max-h-48 overflow-y-auto custom-scrollbar">
            <div
              v-for="(rec, recIdx) in insight.recommendations"
              :key="recIdx"
              class="flex items-center justify-between p-2 bg-white rounded border border-[var(--color-border)] text-xs"
            >
              <div class="flex-1">
                <div class="font-semibold text-[var(--color-fg)]">{{ rec.product_name }}</div>
                <div class="text-[var(--color-fg-muted)]">
                  {{ Math.round(Number(rec.current_price) || 0).toLocaleString(undefined, { maximumFractionDigits: 0 }) }} →
                  <span :class="rec.action === 'increase' ? 'text-red-600' : 'text-emerald-600'">
                    {{ Math.round(Number(rec.recommended_price) || 0).toLocaleString(undefined, { maximumFractionDigits: 0 }) }}
                  </span>
                </div>
              </div>
              <div class="text-right">
                <div :class="rec.action === 'increase' ? 'text-red-600' : 'text-emerald-600'" class="font-bold">
                  {{ rec.action === 'increase' ? '+' : '' }}{{ rec.difference_percent }}%
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="text-center py-8 text-[var(--color-fg-muted)]">
      No insights available. Ensure exchange rate data is logged.
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

const insights = ref([])
const loading = ref(false)

const fetchInsights = async () => {
  loading.value = true
  try {
    const res = await api.get('ai/business-insights/')
    insights.value = res.data.insights || []
  } catch (err) {
    console.error('Failed to fetch business insights:', err)
    insights.value = []
  } finally {
    loading.value = false
  }
}

const refresh = () => {
  fetchInsights()
}

onMounted(() => {
  fetchInsights()
})
</script>

