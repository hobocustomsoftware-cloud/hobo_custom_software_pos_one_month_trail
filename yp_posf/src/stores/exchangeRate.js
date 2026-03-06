import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import api from '@/services/api'

/** Current USD exchange rate for POS (MMK per 1 USD). Used to recalc DYNAMIC_USD product prices. */
export const useExchangeRateStore = defineStore('exchangeRate', () => {
  const usdExchangeRate = ref(null) // number | null

  const hasRate = computed(() => usdExchangeRate.value != null && Number(usdExchangeRate.value) > 0)

  async function fetchExchangeRate() {
    try {
      // api service က auto token injection လုပ်ပေးတယ်
      const { data } = await api.get('settings/exchange-rate/')
      const rate = data.usd_exchange_rate
      usdExchangeRate.value = rate != null ? Number(rate) : null
      return usdExchangeRate.value
    } catch (e) {
      return null
    }
  }

  function setExchangeRate(value) {
    const n = value != null && value !== '' ? Number(value) : null
    usdExchangeRate.value = n > 0 ? n : null
  }

  /** Compute MMK price for a product. If DYNAMIC_USD and cost_usd + rate, return (cost_usd * rate) * (1 + markup/100). */
  function priceInMmk(product) {
    if (!product) return null
    const n = (v) => (v != null && v !== '' ? Number(v) : 0)
    const rate = usdExchangeRate.value
    const priceType = product.price_type
    if (priceType === 'DYNAMIC_USD' && rate > 0 && n(product.cost_usd) > 0) {
      const costUsd = n(product.cost_usd)
      const markup = n(product.markup_percentage) / 100
      return costUsd * rate * (1 + markup)
    }
    return n(product.effective_selling_price_mmk) || n(product.retail_price) || 0
  }

  /** Whether this product's displayed price is coming from USD rate (show $ synced). */
  function isDynamicSynced(product) {
    if (!product) return false
    const rate = usdExchangeRate.value
    return (
      product.price_type === 'DYNAMIC_USD' &&
      rate > 0 &&
      (product.cost_usd != null && product.cost_usd !== '')
    )
  }

  return {
    usdExchangeRate,
    hasRate,
    fetchExchangeRate,
    setExchangeRate,
    priceInMmk,
    isDynamicSynced,
  }
})
