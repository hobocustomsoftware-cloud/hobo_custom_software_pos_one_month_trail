<template>
  <!-- Loyverse-style: white bg, black text, simple and readable -->
  <div class="bg-white rounded-2xl border border-[var(--color-border)] shadow-lg p-6">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-xl font-bold text-[#1a1a1a]">AI ပစ္စည်းအကြံပြုချက်</h3>
      <button
        @click="$emit('close')"
        class="p-2 rounded-lg text-[#4b5563] hover:bg-gray-100 hover:text-[#1a1a1a] transition-colors text-lg font-bold"
        aria-label="ပိတ်မည်"
      >
        ✕
      </button>
    </div>

    <div class="space-y-4">
      <!-- Input Section -->
      <div class="flex flex-wrap gap-3">
        <input
          v-model="query"
          type="text"
          placeholder="ပစ္စည်းရှာပါ (ဥပမာ - Solar inverter 5kW)"
          class="flex-1 min-w-[200px] px-4 py-3 rounded-xl border-2 border-[var(--color-border)] bg-white text-[#1a1a1a] placeholder-[#6b7280] text-base focus:border-[#1078D1] focus:ring-2 focus:ring-[#1078D1]/20"
          @keyup.enter="search"
        />
        <input
          v-model="useCase"
          type="text"
          placeholder="အသုံးပြုမှု (ဥပမာ - အိမ်သုံး solar)"
          class="flex-1 min-w-[200px] px-4 py-3 rounded-xl border-2 border-[var(--color-border)] bg-white text-[#1a1a1a] placeholder-[#6b7280] text-base focus:border-[#1078D1] focus:ring-2 focus:ring-[#1078D1]/20"
          @keyup.enter="search"
        />
        <button
          @click="search"
          :disabled="loading"
          class="min-h-[56px] px-6 py-3 rounded-xl font-bold bg-[#1078D1] text-white hover:bg-[#0d62a8] disabled:opacity-60 transition-colors"
        >
          {{ loading ? 'ရှာနေပါသည်...' : 'ရှာမည်' }}
        </button>
      </div>

      <!-- Results -->
      <div v-if="suggestions.length > 0" class="space-y-3">
        <h4 class="font-semibold text-[#1a1a1a] text-base">အကြံပြုပစ္စည်းများ</h4>
        <div
          v-for="(item, idx) in suggestions"
          :key="idx"
          class="p-4 rounded-xl border-2 border-[var(--color-border)] bg-[#f4f4f4] hover:border-[#1078D1] hover:bg-[#eff6ff] transition-colors cursor-pointer"
          @click="selectProduct(item.product)"
        >
          <div class="flex items-start justify-between gap-4">
            <div class="flex-1 min-w-0">
              <h5 class="font-bold text-[#1a1a1a] text-base mb-1">{{ item.product.name }}</h5>
              <p class="text-sm text-[#4b5563] mb-2">{{ item.match_reason }}</p>
              <div v-if="item.product.specifications && item.product.specifications.length > 0" class="flex flex-wrap gap-2 mt-2">
                <span
                  v-for="spec in item.product.specifications.slice(0, 3)"
                  :key="spec.id"
                  class="px-2 py-1 bg-white rounded border border-[var(--color-border)] text-sm text-[#374151]"
                >
                  {{ spec.label }}: {{ spec.value }}
                </span>
              </div>
              <div class="mt-2 text-lg font-bold text-[#1078D1]">
                {{ Number(item.product.retail_price || 0).toLocaleString() }} ကျပ်
              </div>
            </div>
            <button
              @click.stop="selectProduct(item.product)"
              class="shrink-0 min-h-[44px] px-4 py-2 rounded-xl font-bold bg-[#1078D1] text-white hover:bg-[#0d62a8] transition-colors"
            >
              ထည့်မည်
            </button>
          </div>
        </div>
      </div>

      <!-- Bundles -->
      <div v-if="bundles.length > 0" class="space-y-3 mt-6">
        <h4 class="font-semibold text-[#1a1a1a] text-base">အကြံပြုအစုများ</h4>
        <div
          v-for="bundle in bundles"
          :key="bundle.id"
          class="p-4 rounded-xl border-2 border-[var(--color-border)] bg-[#f4f4f4]"
        >
          <h5 class="font-bold text-[#1a1a1a]">{{ bundle.name }}</h5>
          <p class="text-sm text-[#4b5563]">{{ bundle.description }}</p>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="!loading && query && suggestions.length === 0 && bundles.length === 0" class="text-center py-8 text-[#6b7280] text-base">
        ပစ္စည်းမတွေ့ပါ။ စာသားပြောင်းရှာကြည့်ပါ။
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '@/services/api'

const emit = defineEmits(['close', 'select'])

const query = ref('')
const useCase = ref('')
const loading = ref(false)
const suggestions = ref([])
const bundles = ref([])

const search = async () => {
  if (!query.value.trim() && !useCase.value.trim()) return
  
  loading.value = true
  try {
    const res = await api.post('products/ai-suggest/', {
      query: query.value,
      use_case: useCase.value,
      max_results: 5,
    })
    suggestions.value = res.data.suggestions || []
    bundles.value = res.data.bundles || []
  } catch (err) {
    console.error('AI suggestion failed:', err)
    alert('Failed to get suggestions')
  } finally {
    loading.value = false
  }
}

const selectProduct = (product) => {
  emit('select', product)
  emit('close')
}
</script>
