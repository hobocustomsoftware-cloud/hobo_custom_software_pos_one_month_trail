import { defineStore } from 'pinia'
import api from '@/services/api'

const STORAGE_KEY = 'product_field_settings'

function loadFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return { show_warranty: true, show_expiry_date: true, show_model_number: true, enabled_unit_ids: [] }
    const data = JSON.parse(raw)
    return {
      show_warranty: data.show_warranty !== false,
      show_expiry_date: data.show_expiry_date !== false,
      show_model_number: data.show_model_number !== false,
      enabled_unit_ids: Array.isArray(data.enabled_unit_ids) ? data.enabled_unit_ids : [],
    }
  } catch {
    return { show_warranty: true, show_expiry_date: true, show_model_number: true, enabled_unit_ids: [] }
  }
}

function saveToStorage(data) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  } catch (_) {}
}

export const useProductFieldSettingsStore = defineStore('productFieldSettings', {
  state: () => ({
    show_warranty: true,
    show_expiry_date: true,
    show_model_number: true,
    enabled_unit_ids: [],
    loaded: false,
  }),

  getters: {
    hasEnabledUnitsFilter: (state) => Array.isArray(state.enabled_unit_ids) && state.enabled_unit_ids.length > 0,
  },

  actions: {
    async fetch() {
      try {
        const res = await api.get('settings/product-fields/')
        this.show_warranty = res.data?.show_warranty !== false
        this.show_expiry_date = res.data?.show_expiry_date !== false
        this.show_model_number = res.data?.show_model_number !== false
        this.enabled_unit_ids = Array.isArray(res.data?.enabled_unit_ids) ? res.data.enabled_unit_ids : []
        this.loaded = true
        saveToStorage({
          show_warranty: this.show_warranty,
          show_expiry_date: this.show_expiry_date,
          show_model_number: this.show_model_number,
          enabled_unit_ids: this.enabled_unit_ids,
        })
        return res.data
      } catch (e) {
        const fallback = loadFromStorage()
        this.show_warranty = fallback.show_warranty !== false
        this.show_expiry_date = fallback.show_expiry_date !== false
        this.show_model_number = fallback.show_model_number !== false
        this.enabled_unit_ids = fallback.enabled_unit_ids || []
        this.loaded = true
        return fallback
      }
    },
    async patch(payload) {
      const res = await api.patch('settings/product-fields/', payload)
      this.show_warranty = res.data?.show_warranty !== false
      this.show_expiry_date = res.data?.show_expiry_date !== false
      this.show_model_number = res.data?.show_model_number !== false
      this.enabled_unit_ids = Array.isArray(res.data?.enabled_unit_ids) ? res.data.enabled_unit_ids : []
      saveToStorage({
        show_warranty: this.show_warranty,
        show_expiry_date: this.show_expiry_date,
        show_model_number: this.show_model_number,
        enabled_unit_ids: this.enabled_unit_ids,
      })
      return res.data
    },
  },
})
