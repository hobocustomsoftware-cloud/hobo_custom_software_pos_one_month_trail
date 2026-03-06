<template>
  <!-- Loyverse-style: white bg, black text, simple and readable -->
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="isOpen"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
        @click.self="close"
      >
        <div class="bg-white w-full max-w-2xl rounded-2xl p-6 border-2 border-[var(--color-border)] shadow-xl">
          <!-- Header -->
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-xl font-bold text-[#1a1a1a]">ဒေါ်လာဈေးနှုန်း ချိန်ညှိရန်</h2>
            <button
              @click="close"
              class="p-2 rounded-lg text-[#4b5563] hover:bg-gray-100 hover:text-[#1a1a1a] transition-colors"
              aria-label="ပိတ်မည်"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Toggle: ဗဟိုဘဏ်မှ ဆွဲမည် (Auto) vs ကိုယ်ထိလက်ရောက်ပြင်မည် (Manual) -->
          <div class="mb-6">
            <label class="flex items-center justify-between p-4 rounded-xl bg-[#f4f4f4] border-2 border-[var(--color-border)] cursor-pointer hover:bg-gray-100 transition-all">
              <div>
                <div class="text-base font-bold text-[#1a1a1a] mb-1">ဗဟိုဘဏ် (CBM) မှ အလိုအလျောက်ဆွဲမည်</div>
                <div class="text-sm text-[#4b5563]">
                  {{ localIsAutoSync ? 'မြန်မာဗဟိုဘဏ် ဝဘ်မှ ဒေါ်လာဈေးနှုန်း ယူသုံးမည်' : 'ကိုယ်ထိလက်ရောက် ထည့်ထားသော ဈေးနှုန်းသုံးမည်' }}
                </div>
              </div>
              <div class="relative">
                <input
                  v-model="localIsAutoSync"
                  type="checkbox"
                  class="sr-only"
                  @change="handleToggleChange"
                />
                <div
                  class="w-14 h-7 rounded-full transition-all duration-300"
                  :class="localIsAutoSync ? 'bg-[#16a34a]' : 'bg-[#dc2626]'"
                >
                  <div
                    class="w-6 h-6 bg-white rounded-full shadow-lg transform transition-transform duration-300 mt-0.5"
                    :class="localIsAutoSync ? 'translate-x-7' : 'translate-x-0.5'"
                  ></div>
                </div>
              </div>
            </label>
          </div>

          <!-- Manual Rate Input (when Manual mode) -->
          <div v-if="!localIsAutoSync" class="mb-6">
            <label class="block text-base font-bold text-[#1a1a1a] mb-2">ကိုယ်ထိလက်ရောက် ဒေါ်လာဈေး (ကျပ်)</label>
            <input
              v-model="localManualRateStr"
              type="text"
              inputmode="decimal"
              class="w-full min-h-[56px] px-4 py-3 rounded-xl border-2 border-[var(--color-border)] bg-white text-[#1a1a1a] placeholder-[#6b7280] text-lg font-semibold focus:border-[#1078D1] focus:ring-2 focus:ring-[#1078D1]/20"
              placeholder="ဥပမာ ၂၁၀၀"
              @input="onManualRateInput"
            />
            <div class="text-sm text-[#4b5563] mt-1">၁ ဒေါ်လာ = ကျပ်နှုန်း ထည့်ပါ။ ဈေးပြောင်းရင် DYNAMIC_USD ပစ္စည်းဈေးများ အလိုအလျောက်ပြောင်းမည်။</div>
          </div>

          <!-- Market Margin % (optional) -->
          <div class="mb-6">
            <label class="block text-base font-bold text-[#1a1a1a] mb-2">
              ဈေးနှုန်းထပ်ထည့် % <span class="text-[#6b7280] font-normal">(ရွေးမည်)</span>
            </label>
            <input
              v-model="localMarketMarginStr"
              type="text"
              inputmode="decimal"
              class="w-full min-h-[48px] px-4 py-2 rounded-xl border-2 border-[var(--color-border)] bg-white text-[#1a1a1a] placeholder-[#6b7280] text-base focus:border-[#1078D1] focus:ring-2 focus:ring-[#1078D1]/20"
              placeholder="ဥပမာ 5 = +5%"
              @input="onMarketMarginInput"
            />
            <div class="text-sm text-[#4b5563] mt-1">CBM ဈေးနှုန်းအပေါ် ထပ်ထည့်မည့် ရာခိုင်နှုန်း (5 = +5%, -2 = -2%)</div>
          </div>

          <!-- Preview: Product price sync -->
          <div class="mb-6 p-4 rounded-xl bg-[#f4f4f4] border-2 border-[var(--color-border)]">
            <div class="text-base font-bold text-[#1a1a1a] mb-2">ပစ္စည်းဈေး ပြောင်းမည့်အရေအတွက်</div>
            <div class="text-sm text-[#4b5563]">
              <span class="font-bold text-[#1a1a1a]">{{ affectedProductsCount }}</span> ခု (DYNAMIC_USD ပစ္စည်း) ၏ ဈေးများ ဒေါ်လာဈေးပြောင်းတိုင်း အလိုအလျောက်ပြောင်းမည်။
            </div>
            <div v-if="previewRate" class="mt-2 text-sm font-semibold text-[#1a1a1a]">
              လက်ရှိအသုံးပြုမည့်နှုန်း: <span class="text-[#1078D1]">{{ previewRate.toLocaleString() }} ကျပ်</span>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-3">
            <button
              @click="saveSettings"
              :disabled="saving"
              class="flex-1 min-h-[56px] rounded-xl font-bold bg-[#1078D1] text-white hover:bg-[#0d62a8] disabled:opacity-60 transition-colors"
            >
              <span v-if="saving">သိမ်းနေပါသည်...</span>
              <span v-else>သိမ်းမည်</span>
            </button>
            <button
              @click="close"
              class="min-h-[56px] px-6 rounded-xl font-bold border-2 border-[var(--color-border)] text-[#1a1a1a] hover:bg-gray-100 transition-colors"
            >
              မလုပ်ပါ
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import api from '@/services/api'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
})

const emit = defineEmits(['update:isOpen', 'saved'])

const localIsAutoSync = ref(true)
const localManualRate = ref(null)
const localMarketMargin = ref(null)
const localManualRateStr = ref('')
const localMarketMarginStr = ref('')

function numericInputStr(val, allowNegative = false) {
  let s = String(val).replace(/[^\d.-]/g, '')
  if (!allowNegative) s = s.replace(/-/g, '')
  else if (s.startsWith('-')) s = '-' + s.slice(1).replace(/-/g, '')
  const parts = s.split('.')
  if (parts.length > 2) s = parts[0] + '.' + parts.slice(1).join('')
  return s
}
const onManualRateInput = () => {
  localManualRateStr.value = numericInputStr(localManualRateStr.value, false)
  const n = parseFloat(localManualRateStr.value)
  localManualRate.value = Number.isFinite(n) ? n : null
  loadAffectedProductsCount()
}
const onMarketMarginInput = () => {
  localMarketMarginStr.value = numericInputStr(localMarketMarginStr.value, true)
  const n = parseFloat(localMarketMarginStr.value)
  localMarketMargin.value = Number.isFinite(n) ? n : null
  loadAffectedProductsCount()
}
const saving = ref(false)
const affectedProductsCount = ref(0)
const previewRate = ref(null)

const close = () => {
  emit('update:isOpen', false)
}

const handleToggleChange = () => {
  // Toggle ပြောင်းရင် preview ပဲ ပြန်တွက်မယ်၊ server ကနေ ပြန်မဖတ်ဘူး (ပိတ်ထားရင် ပြန်မပွင့်အောင်)
  loadAffectedProductsCount()
}

const loadCurrentSettings = async () => {
  try {
    const res = await api.get('settings/exchange-rate/')
    localIsAutoSync.value = res.data.is_auto_sync !== false
    const manual = res.data.manual_usd_rate ? parseFloat(res.data.manual_usd_rate) : null
    localManualRate.value = manual
    localManualRateStr.value = manual != null ? String(manual) : ''

    try {
      const adjRes = await api.get('settings/exchange-rate/adjustments/')
      if (adjRes.data.usd?.market_premium_percentage) {
        const margin = parseFloat(adjRes.data.usd.market_premium_percentage)
        localMarketMargin.value = margin
        localMarketMarginStr.value = String(margin)
      } else {
        localMarketMargin.value = null
        localMarketMarginStr.value = ''
      }
    } catch (e) {
      localMarketMargin.value = null
      localMarketMarginStr.value = ''
    }

    await loadAffectedProductsCount()
  } catch (err) {
    console.error('Failed to load exchange rate settings:', err)
  }
}

const loadAffectedProductsCount = async () => {
  try {
    // Get count of DYNAMIC_USD products
    const res = await api.get('products-admin/', { params: { price_type: 'DYNAMIC_USD', page_size: 1 } })
    affectedProductsCount.value = res.data.count || 0
    
    // Calculate preview rate
    if (localIsAutoSync.value) {
      // Use current rate from store
      const rateRes = await api.get('settings/exchange-rate/')
      if (rateRes.data.usd_exchange_rate) {
        let rate = parseFloat(rateRes.data.usd_exchange_rate)
        if (localMarketMargin.value) {
          rate = rate * (1 + localMarketMargin.value / 100)
        }
        previewRate.value = rate
      }
    } else if (localManualRate.value) {
      previewRate.value = localManualRate.value
    }
  } catch (err) {
    console.error('Failed to load affected products count:', err)
  }
}

const saveSettings = async () => {
  saving.value = true
  try {
    // Save is_auto_sync and manual_usd_rate — backend auto-syncs DYNAMIC_USD item prices
    const patchRes = await api.patch('settings/exchange-rate/', {
      is_auto_sync: localIsAutoSync.value,
      manual_usd_rate: localIsAutoSync.value ? null : localManualRate.value,
    })
    const synced = patchRes?.data?.prices_synced_count
    if (synced != null && synced > 0) {
      // Show feedback that item prices were updated
      alert(`ဒေါ်လာဈေးနှုန်း သိမ်းပြီး။ DYNAMIC_USD ပစ္စည်း ${synced} ခု ၏ ဈေးများ အလိုအလျောက်ပြောင်းပြီး။`)
    }

    // Save market margin if provided
    if (localMarketMargin.value !== null) {
      await api.post('settings/exchange-rate/adjustments/', {
        usd: {
          market_premium_percentage: localMarketMargin.value,
          manual_fixed_rate: null,
        },
      })
    }

    emit('saved')
    close()
  } catch (err) {
    console.error('Failed to save exchange rate settings:', err)
    alert('Failed to save settings. Please try again.')
  } finally {
    saving.value = false
  }
}

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    loadCurrentSettings()
  }
})

watch([localIsAutoSync, localManualRate, localMarketMargin], () => {
  loadAffectedProductsCount()
})
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
