import { defineStore } from 'pinia'

const STORAGE_KEY = 'pos_features'

const defaultFeatures = () => ({
  enableTax: false,
  enableDiscount: true,
  enableLoyalty: false,
  requireSaleApproval: true,
  showUsdRate: true,
})

function loadFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return defaultFeatures()
    const parsed = JSON.parse(raw)
    return { ...defaultFeatures(), ...parsed }
  } catch {
    return defaultFeatures()
  }
}

function saveToStorage(features) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(features))
  } catch (_) {}
}

export const usePosFeaturesStore = defineStore('posFeatures', {
  state: () => loadFromStorage(),

  actions: {
    setEnableTax(value) {
      this.enableTax = !!value
      saveToStorage(this.$state)
    },
    setEnableDiscount(value) {
      this.enableDiscount = !!value
      saveToStorage(this.$state)
    },
    setEnableLoyalty(value) {
      this.enableLoyalty = !!value
      saveToStorage(this.$state)
    },
    setRequireSaleApproval(value) {
      this.requireSaleApproval = !!value
      saveToStorage(this.$state)
    },
    setShowUsdRate(value) {
      this.showUsdRate = !!value
      saveToStorage(this.$state)
    },
    load() {
      const loaded = loadFromStorage()
      this.enableTax = loaded.enableTax
      this.enableDiscount = loaded.enableDiscount
      this.enableLoyalty = loaded.enableLoyalty
      this.requireSaleApproval = loaded.requireSaleApproval !== false
      this.showUsdRate = loaded.showUsdRate !== false
    },
  },
})
