<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-100 via-slate-50 to-amber-50/30 px-4 py-8">
    <div class="max-w-md w-full bg-white rounded-3xl shadow-xl border border-slate-200/60 p-8">
      <div class="text-center mb-8">
        <h2 class="text-2xl font-black text-slate-800 tracking-tight">စကားဝှက် ပြန်သတ်မှတ်ရန်</h2>
        <p class="text-slate-500 text-sm mt-1">စကားဝှက် အသစ် ထည့်ပါ</p>
      </div>

      <form v-if="!success" @submit.prevent="handleSubmit" class="space-y-4">
        <div>
          <label class="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">စကားဝှက် အသစ်</label>
          <input
            v-model="newPassword"
            type="password"
            required
            minlength="6"
            class="w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-amber-400/50 focus:border-amber-400 outline-none transition-all"
            placeholder="••••••••"
          />
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">စကားဝှက် ပြန်ရိုက်ပါ</label>
          <input
            v-model="confirmPassword"
            type="password"
            required
            class="w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-amber-400/50 focus:border-amber-400 outline-none transition-all"
            placeholder="••••••••"
          />
        </div>
        <button
          type="submit"
          :disabled="loading"
          class="w-full py-3.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 text-white font-bold shadow-lg disabled:opacity-70"
        >
          {{ loading ? 'ပြောင်းလဲနေပါသည်...' : 'ပြောင်းလဲရန်' }}
        </button>
        <p v-if="error" class="text-rose-600 text-sm text-center">{{ error }}</p>
      </form>

      <div v-else class="space-y-4">
        <p class="text-emerald-600 text-sm font-medium text-center">{{ success }}</p>
        <RouterLink
          to="/login"
          class="block w-full py-3.5 rounded-xl bg-amber-500 text-white font-bold text-center hover:bg-amber-600 transition"
        >
          ဝင်ရောက်ရန်
        </RouterLink>
      </div>

      <p class="mt-6 text-center text-sm text-slate-500">
        <RouterLink to="/login" class="font-bold text-amber-600 hover:text-amber-700">ဝင်ရောက်ရန်</RouterLink>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import api from '@/services/api'

const route = useRoute()
const token = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const error = ref('')
const success = ref('')

onMounted(() => {
  token.value = route.query.token || ''
  if (!token.value) error.value = 'Token မရှိပါ။ Forgot Password မှ ထပ်မံတောင်းခံပါ။'
})

const handleSubmit = async () => {
  if (newPassword.value !== confirmPassword.value) {
    error.value = 'စကားဝှက် မကိုက်ညီပါ။'
    return
  }
  if (newPassword.value.length < 6) {
    error.value = 'စကားဝှက် အနည်းဆုံး ၆ လုံး ရှိရပါမည်။'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const res = await api.post('core/reset-password/', {
      token: token.value,
      new_password: newPassword.value,
    })
    success.value = res.data?.message || 'စကားဝှက် ပြောင်းလဲပြီးပါပြီ။'
  } catch (e) {
    error.value = e.response?.data?.error || 'မအောင်မြင်ပါ။'
  } finally {
    loading.value = false
  }
}
</script>
