<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-100 via-slate-50 to-amber-50/30 px-4 py-8">
    <div class="max-w-md w-full bg-white rounded-3xl shadow-xl border border-slate-200/60 p-8">
      <div class="text-center mb-8">
        <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-amber-100 flex items-center justify-center">
          <svg class="w-8 h-8 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
          </svg>
        </div>
        <h2 class="text-2xl font-bold text-gray-800">License Activation</h2>
        <p class="text-gray-500 mt-2">{{ message || 'License key ထည့်သွင်းပြီး Activate လုပ်ပါ။' }}</p>
      </div>

      <form @submit.prevent="handleActivate" class="space-y-6">
        <div>
          <label class="block text-sm font-medium text-gray-700">License Key</label>
          <input
            v-model="licenseKey"
            type="text"
            required
            class="mt-1 block w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-amber-400/50 focus:border-amber-400 outline-none transition-all"
            placeholder="WLD-XXXXXXXX-XXXX"
          />
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full flex justify-center py-3.5 px-4 rounded-xl shadow-lg text-white bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 font-bold transition-all disabled:opacity-70"
        >
          {{ loading ? 'Activating...' : 'Activate' }}
        </button>

        <p v-if="error" class="text-rose-600 text-center text-sm">{{ error }}</p>
        <p v-if="success" class="text-emerald-600 text-center text-sm font-medium">{{ success }}</p>
      </form>

      <p class="mt-6 text-center text-sm text-slate-500">
        License မဝယ်ရသေးလား? ဆက်သွယ်ပါ။
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getLoginPath } from '@/router'
import api from '@/services/api'

const router = useRouter()
const licenseKey = ref('')
const loading = ref(false)
const error = ref('')
const success = ref('')
const message = ref('')

onMounted(async () => {
  try {
    const res = await api.get('license/status/')
    const data = res.data
    if (data.status === 'blocked' || data.status === 'expired') {
      message.value = data.message || 'License သက်တမ်းကုန်ပြီးပါပြီ။'
    } else if (data.status === 'grace') {
      message.value = `${data.days_remaining} ရက်အတွင်း License ဝယ်ပါ။`
    }
  } catch (_) {
    message.value = 'License key ထည့်သွင်းပြီး Activate လုပ်ပါ။'
  }
})

async function handleActivate() {
  if (!licenseKey.value.trim()) return
  loading.value = true
  error.value = ''
  success.value = ''
  try {
    const res = await api.post('license/activate/', { license_key: licenseKey.value.trim() })
    if (res.data.message) {
      success.value = res.data.message
      setTimeout(() => router.push(getLoginPath()), 1500)
    }
  } catch (err) {
    error.value = err.response?.data?.error || err.response?.data?.message || 'Activation မအောင်မြင်ပါ။'
  } finally {
    loading.value = false
  }
}
</script>
