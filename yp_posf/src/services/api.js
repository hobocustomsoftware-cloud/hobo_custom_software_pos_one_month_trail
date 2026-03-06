import axios from 'axios'
import { API_URL } from '@/config'
import router, { getLoginPath, getAppPath } from '@/router'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'

const api = axios.create({
  baseURL: API_URL,
})

// Request တိုင်းမှာ Token ပါသွားအောင် လုပ်ခြင်း
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 403 license_expired → License Activation; trial_expired → Trial Expired page with contact
// 401 → logout and login; 500/503 → toast so UI does not stay blank
// Network error (ERR_CONNECTION_REFUSED, etc.): no err.response
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (!err.response) {
      const toast = useToast()
      toast.error('ဆာဗာနဲ့ ချိတ်ဆက်၍ မရပါ။ အင်တာနက်စစ်ပါ သို့မဟုတ် ဆာဗာ ဖွင့်ပါ။')
      return Promise.reject(err)
    }
    // 400 with HTML body = Django ALLOWED_HOSTS block (e.g. Google instance IP not in list)
    const status = err.response?.status
    const data = err.response?.data
    if (status === 400 && typeof data === 'string' && (data.includes('Bad Request') || data.includes('<!doctype'))) {
      err.response.data = {
        detail: 'Server configuration error. On Google Cloud / VPS: add this server\'s IP or domain to DJANGO_ALLOWED_HOSTS in .env and restart the backend. / ဆာဗာ IP သို့မဟုတ် domain ကို .env ထဲက DJANGO_ALLOWED_HOSTS မှာ ထည့်ပြီး backend ပြန် start ပါ။',
      }
    }
    if (err.response?.status === 403 && err.response?.data?.error === 'license_expired') {
      router.push(getAppPath('/license-activate'))
      return Promise.reject(err)
    }
    if (err.response?.status === 403 && err.response?.data?.error === 'trial_expired') {
      const contact = err.response?.data?.contact || ''
      router.push({ path: getAppPath('/trial-expired'), query: contact ? { contact: encodeURIComponent(contact) } : {} })
      return Promise.reject(err)
    }
    if (status === 401) {
      const isLoginRequest = err.config?.url?.includes('auth/login')
      useAuthStore().logout()
      // Don't redirect if 401 came from login attempt (show error on login page)
      if (!isLoginRequest && router.currentRoute?.value?.meta?.public !== true) {
        router.push(getLoginPath())
      }
    }
    const toast = useToast()
    // 500, 503: show toast so user sees feedback instead of blank/failed state
    if (status === 500 || status === 503) {
      const msg = status === 503
        ? 'ဆာဗာ ယာယီမရပါ။ ခဏကြာပြီး ထပ်ကြိုးစားပါ။'
        : 'ဆာဗာအမှား ဖြစ်ပါသည်။ ထပ်ကြိုးစားပါ။'
      toast.error(msg)
    }
    // 403 (generic permission): show message when not license/trial
    if (status === 403 && err.response?.data?.error !== 'license_expired' && err.response?.data?.error !== 'trial_expired') {
      toast.error(err.response?.data?.detail || 'ခွင့်ပြုချက် မရှိပါ။')
    }
    // 404: leave to callers to show inline error (avoid duplicate toasts)
    return Promise.reject(err)
  }
)

export default api
