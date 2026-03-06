import { defineStore } from 'pinia'
import api from '@/services/api'

const STORAGE_KEY = 'feature_toggles'

function loadFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return { enable_service: true, enable_installation: true, enable_treatment_records: true }
    return { enable_service: true, enable_installation: true, enable_treatment_records: true, ...JSON.parse(raw) }
  } catch {
    return { enable_service: true, enable_installation: true, enable_treatment_records: true }
  }
}

function saveToStorage(data) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  } catch (_) {}
}

export const useFeatureTogglesStore = defineStore('featureToggles', {
  state: () => ({
    enable_service: true,
    enable_installation: true,
    enable_treatment_records: true,
    loaded: false,
  }),

  actions: {
    async fetch() {
      try {
        const res = await api.get('settings/service-installation/')
        this.enable_service = res.data?.enable_service !== false
        this.enable_installation = res.data?.enable_installation !== false
        this.enable_treatment_records = res.data?.enable_treatment_records !== false
        this.loaded = true
        saveToStorage({ enable_service: this.enable_service, enable_installation: this.enable_installation, enable_treatment_records: this.enable_treatment_records })
        return res.data
      } catch (e) {
        const fallback = loadFromStorage()
        this.enable_service = fallback.enable_service !== false
        this.enable_installation = fallback.enable_installation !== false
        this.enable_treatment_records = fallback.enable_treatment_records !== false
        this.loaded = true
        return { enable_service: this.enable_service, enable_installation: this.enable_installation, enable_treatment_records: this.enable_treatment_records }
      }
    },
    async patch(payload) {
      const res = await api.patch('settings/service-installation/', payload)
      this.enable_service = res.data?.enable_service !== false
      this.enable_installation = res.data?.enable_installation !== false
      this.enable_treatment_records = res.data?.enable_treatment_records !== false
      saveToStorage({ enable_service: this.enable_service, enable_installation: this.enable_installation, enable_treatment_records: this.enable_treatment_records })
      return res.data
    },
  },
})
