<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-100 via-slate-50 to-amber-50/30 px-4 py-8">
    <div class="max-w-md w-full bg-white rounded-3xl shadow-xl border border-slate-200/60 p-8">
      <div class="text-center mb-8">
        <h2 class="text-2xl font-black text-slate-800 tracking-tight">စကားဝှက် မေ့သွားပါသလား</h2>
        <p class="text-slate-500 text-sm mt-1">Username ထည့်ပြီး Reset link ရယူပါ</p>
      </div>

      <form v-if="!success" @submit.prevent="handleSubmit" class="space-y-4">
        <div>
          <label class="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">Username</label>
          <input
            v-model="username"
            type="text"
            required
            class="w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-amber-400/50 focus:border-amber-400 outline-none transition-all"
            placeholder="username"
          />
        </div>
        <button
          type="submit"
          :disabled="loading"
          class="w-full py-3.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 text-white font-bold shadow-lg disabled:opacity-70"
        >
          {{ loading ? 'စစ်ဆေးနေပါသည်...' : 'Reset Link ရယူရန်' }}
        </button>
        <p v-if="error" class="text-rose-600 text-sm text-center">{{ error }}</p>
      </form>

      <div v-else class="space-y-4">
        <p class="text-emerald-600 text-sm font-medium">{{ success }}</p>
        <RouterLink
          :to="{ path: '/reset-password', query: { token: resetToken } }"
          class="block w-full py-3.5 rounded-xl bg-amber-500 text-white font-bold text-center hover:bg-amber-600 transition"
        >
          စကားဝှက် ပြန်သတ်မှတ်ရန် သွားပါ
        </RouterLink>
      </div>

      <p class="mt-6 text-center text-sm text-slate-500">
        <RouterLink to="/login" class="font-bold text-amber-600 hover:text-amber-700">ဝင်ရောက်ရန်</RouterLink>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import api from '@/services/api'

const router = useRouter()
const username = ref('')
const loading = ref(false)
const error = ref('')
const success = ref('')
const resetToken = ref('')

const handleSubmit = async () => {
  loading.value = true
  error.value = ''
  success.value = ''
  try {
    const res = await api.post('core/forgot-password/', { username: username.value })
    success.value = res.data?.message || 'Reset link ရရှိပါပြီ။'
    resetToken.value = res.data?.token || ''
  } catch (e) {
    error.value = e.response?.data?.error || 'မအောင်မြင်ပါ။ ထပ်ကြိုးစားပါ။'
  } finally {
    loading.value = false
  }
}
</script>
