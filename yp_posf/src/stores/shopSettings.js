import { defineStore } from 'pinia'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'

export const useShopSettingsStore = defineStore('shopSettings', {
  state: () => ({
    shop_name: 'HoBo POS',
    logo_url: null,
    loaded: false,
    /** Loyverse-style: true after first-time setup wizard completed */
    setup_wizard_done: false,
    /** pharmacy | pharmacy_clinic | mobile | computer | solar | hardware | liquor | grocery | general - for unit filtering */
    business_category: null,
    /** true = only show units for business_category; false = show all units */
    filter_units_by_business_category: true,
    /** 404 / API မရှိရင် true - UI မှာ Backend စတင်ရန် သတိပေးသုံးမယ် */
    apiUnavailable: false,
  }),

  actions: {
    async fetch() {
      if (!useAuthStore().token) {
        this.loaded = true
        return null
      }
      try {
        const res = await api.get('core/shop-settings/')
        this.shop_name = res.data.shop_name || 'HoBo POS'
        this.logo_url = res.data.logo_url || null
        this.setup_wizard_done = !!res.data.setup_wizard_done
        this.business_category = res.data.business_category || null
        this.filter_units_by_business_category = res.data.filter_units_by_business_category !== false
        this.loaded = true
        this.apiUnavailable = false
        return res.data
      } catch (e) {
        this.loaded = true
        this.apiUnavailable = e.response?.status === 404 || !e.response
        return null
      }
    },

    async update(data) {
      try {
        const formData = new FormData()
        if (data.shop_name != null) formData.append('shop_name', data.shop_name)
        if (data.logo && data.logo instanceof File) formData.append('logo', data.logo)
        if (data.setup_wizard_done !== undefined) formData.append('setup_wizard_done', data.setup_wizard_done ? 'true' : 'false')
        if (data.business_category != null) formData.append('business_category', data.business_category)
        if (data.currency != null) formData.append('currency', data.currency)
        if (data.filter_units_by_business_category !== undefined) formData.append('filter_units_by_business_category', data.filter_units_by_business_category ? 'true' : 'false')

        // Do not set Content-Type: let browser set multipart/form-data with boundary so file upload works
        const res = await api.put('core/shop-settings/', formData)
        this.shop_name = res.data.shop_name || 'HoBo POS'
        this.logo_url = res.data.logo_url || null
        this.setup_wizard_done = !!res.data.setup_wizard_done
        this.business_category = res.data.business_category || null
        this.filter_units_by_business_category = res.data.filter_units_by_business_category !== false
        return res.data
      } catch (e) {
        this.apiUnavailable = e.response?.status === 404 || !e.response
        throw e
      }
    },
  },

  getters: {
    displayName: (state) => state.shop_name || 'HoBo POS',
    logo: (state) => state.logo_url,
  },
})
