import { defineStore } from 'pinia'
import api from '@/services/api'

const VALID_TYPES = ['phone_electronics', 'pharmacy_clinic', 'hardware_store', 'solar_aircon', 'general_retail']

export const useBusinessTypeStore = defineStore('businessType', {
  state: () => ({
    business_type: 'general_retail',
    loaded: false,
  }),

  getters: {
    isPhoneMode: (state) => state.business_type === 'phone_electronics',
    isPharmacyMode: (state) => state.business_type === 'pharmacy_clinic',
    isHardwareMode: (state) => state.business_type === 'hardware_store',
    isSolarAirconMode: (state) => state.business_type === 'solar_aircon',
    isGeneralRetail: (state) => state.business_type === 'general_retail',

    /** Universal Myanmar Cloud POS: Industry Engine
     * Pharmacy: 3-level units + Expiry. Hide Serial.
     * Solar/AC: Bundle + Site Survey + Serial.
     * Phone/PC: Serial (IMEI) only. Hide Multi-Units.
     * Hardware: Dozen/Bulk + Credit payment.
     */
    serialTracking: (state) =>
      state.business_type === 'phone_electronics' || state.business_type === 'solar_aircon',
    warrantyLogic: (state) => state.business_type === 'phone_electronics',

    /** Pharmacy: 3-level Units (လုံး/ကတ်/ဗူး) + Expiry. No Serial. */
    multiUnit: (state) => state.business_type === 'pharmacy' || state.business_type === 'pharmacy_clinic',
    batchNoTracking: (state) => state.business_type === 'pharmacy_clinic',
    expiryTracking: (state) => state.business_type === 'pharmacy_clinic',

    /** Hardware: Dozen/Bulk + Credit (အကြွေး) */
    unitConversion: (state) => state.business_type === 'hardware_store',
    wholesaleCreditTracking: (state) => state.business_type === 'hardware_store',

    /** Solar/AC: Bundle Editor + Site Survey + Serial */
    siteSurvey: (state) => state.business_type === 'solar_aircon',
    bundleEditor: (state) => state.business_type === 'solar_aircon',
  },

  actions: {
    async fetch() {
      try {
        const res = await api.get('settings/business-type/')
        const v = res.data?.business_type || 'general_retail'
        this.business_type = VALID_TYPES.includes(v) ? v : 'general_retail'
        this.loaded = true
        return this.business_type
      } catch (e) {
        this.business_type = 'general_retail'
        this.loaded = true
        return this.business_type
      }
    },

    async setBusinessType(value) {
      if (!VALID_TYPES.includes(value)) return
      try {
        await api.patch('settings/business-type/', { business_type: value })
        this.business_type = value
        return true
      } catch (e) {
        throw e
      }
    },
  },
})
