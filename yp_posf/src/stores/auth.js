import { defineStore } from 'pinia'
import api from '@/services/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    // LocalStorage မှ data များကို Initial load လုပ်ခြင်း
    user: JSON.parse(localStorage.getItem('user')) || null,
    token: localStorage.getItem('access_token') || null,
    role: localStorage.getItem('user_role') || null,
  }),

  actions: {
    // ၁။ Login ဝင်ခြင်း - Phone number only in single "login" field
    async login(loginValue, password, countryCode = '+95') {
      try {
        const response = await api.post('core/auth/login/', {
          login: (loginValue || '').trim(),
          password: password || '',
          country_code: countryCode,
        })

        const data = response.data
        this.token = data.access
        localStorage.setItem('access_token', this.token)
        if (data.refresh) localStorage.setItem('refresh_token', data.refresh)
        if (data.user) {
          this.user = data.user
          this.role = data.user.role || data.user.role_name
          localStorage.setItem('user', JSON.stringify(data.user))
          localStorage.setItem('user_role', this.role || '')
        }
        if (data.outlet) {
          localStorage.setItem('outlet', JSON.stringify(data.outlet))
        }

        return true
      } catch (error) {
        console.error('Login Error:', error.response?.data)
        throw error
      }
    },

    // ၂။ လက်ရှိ User ရဲ့ အချက်အလက်နှင့် Role ကို ရယူခြင်း
    async fetchUserProfile() {
      if (!this.token) return

      try {
        // api service က auto token injection လုပ်ပေးတယ်
        const response = await api.get('core/me/')

        // Backend မှလာသော role_name အား သိမ်းဆည်းခြင်း
        this.user = response.data
        this.role = response.data.role_name // ဥပမာ - "super_admin"

        // LocalStorage တွင် Backup အနေဖြင့် သိမ်းခြင်း
        localStorage.setItem('user', JSON.stringify(this.user))
        localStorage.setItem('user_role', this.role)
      } catch (error) {
        console.error('Fetch Profile Error:', error)
        // Token သက်တမ်းကုန်လျှင် Logout လုပ်ပစ်ခြင်း
        if (error.response?.status === 401) {
          this.logout()
        }
      }
    },

    // ၃။ Logout လုပ်ခြင်း
    logout() {
      this.user = null
      this.token = null
      this.role = null
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user_role')
      localStorage.removeItem('user')
      localStorage.removeItem('outlet')
    },
  },
})
