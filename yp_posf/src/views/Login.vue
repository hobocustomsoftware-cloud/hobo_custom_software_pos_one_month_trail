<template>
  <div class="auth-page login-loyverse">
    <div class="auth-card">
      <div class="auth-lang-toggle">
        <button type="button" class="auth-lang-btn" :class="{ active: locale.isEn }" @click="locale.setLang('en')">EN</button>
        <button type="button" class="auth-lang-btn" :class="{ active: locale.isMm }" @click="locale.setLang('mm')">မြန်မာ</button>
      </div>
      <div class="text-center mb-6">
        <img v-show="!logoError && shopLogo" :src="shopLogo" alt="Logo" class="login-logo mx-auto mb-4" @error="logoError=true" />
        <img v-show="!logoError && !shopLogo && !logoSvgFallback" :src="defaultLogo" alt="Logo" class="login-logo mx-auto mb-4" @error="logoSvgFallback=true" />
        <img v-show="!logoError && !shopLogo && logoSvgFallback" :src="fallbackLogo" alt="Logo" class="login-logo mx-auto mb-4" @error="logoError=true" />
        <span v-show="logoError" class="block font-semibold text-[var(--color-primary)] mb-4">{{ shopName }}</span>
        <h1 class="font-semibold text-[#000000] mb-1">{{ t.signIn }}</h1>
        <p class="text-[#374151]">{{ t.signInSub }}</p>
      </div>

      <form @submit.prevent="handleLogin" class="space-y-4">
        <div>
          <label class="auth-label block mb-1.5 font-medium text-[#000000]">{{ t.emailOrPhone }}</label>
          <input v-model="login" type="tel" required class="auth-input login-input auth-input-text block w-full" :placeholder="locale.isEn ? '09xxxxxxxx or +959xxxxxxxx' : '၀၉xxxxxxxx သို့မဟုတ် +၉၅၉xxxxxxxx'" autocomplete="tel" />
        </div>
        <div>
          <label class="auth-label block mb-1.5 font-medium text-[#000000]">{{ t.password }}</label>
          <input v-model="password" type="password" required class="auth-input login-input auth-input-text block w-full" placeholder="••••••••" />
        </div>
        <button type="submit" :disabled="loading" class="auth-btn w-full flex justify-center items-center gap-2">
          <span v-if="loading" class="flex items-center gap-2">
            <svg class="animate-spin w-[1.2em] h-[1.2em]" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ t.signingIn }}
          </span>
          <span v-else>{{ t.signIn }}</span>
        </button>

        <p v-if="error" class="text-[#b91c1c] text-center mt-3 font-medium">{{ error }}</p>
        <p v-if="error && (error.includes('စာရင်းမသွင်းရသေးရင်') || error.includes('Register'))" class="text-center mt-2">
          <RouterLink to="/register" class="auth-link font-medium underline">{{ locale.isMm ? 'စာရင်းသွင်းရန်' : 'Register here' }}</RouterLink>
        </p>
        <div class="space-y-2 pt-3 text-center">
          <p><RouterLink to="/register" class="auth-link font-medium">{{ locale.isEn ? 'Create account' : 'အကောင့်ဖွင့်ရန်' }}</RouterLink></p>
          <p><RouterLink to="/forgot-password" class="auth-link font-medium">{{ t.forgotPassword }}</RouterLink></p>
        </div>
        <p v-if="shopStore.apiUnavailable" class="text-[#b45309] text-center mt-3 font-medium">{{ locale.isEn ? 'Backend not connected. Please start the server.' : 'Backend ချိတ်ဆက်မှု မရပါ။ ဆာဗာစတင်ပါ။' }}</p>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useShopSettingsStore } from '@/stores/shopSettings'
import { useLocaleStore } from '@/stores/locale'
import { authLabels } from '@/stores/locale'

const locale = useLocaleStore()
const t = computed(() => authLabels[locale.lang])

const base = (import.meta.env.BASE_URL || '/').replace(/\/$/, '') + '/'
const defaultLogo = base + 'logo.png'
const fallbackLogo = base + 'logo.svg'
const logoError = ref(false)
const logoSvgFallback = ref(false)
const shopStore = useShopSettingsStore()
const shopLogo = computed(() => shopStore.logo_url)
const shopName = computed(() => shopStore.displayName)
import { useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'

const authStore = useAuthStore()
const router = useRouter()
const login = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

function getLoginErrorMessage(err) {
  const status = err.response?.status
  const detail = err.response?.data?.detail
  const msg = typeof detail === 'string' ? detail : (Array.isArray(detail) ? detail[0] : '')

  // Backend မရှိ / ချိတ်ဆက်မှု မရ (network error, 502, 503)
  if (!err.response || status === 0 || status >= 502) {
    return 'Backend ချိတ်ဆက်မှု မရပါ။ Backend (Django) စတင်ထားပါ။'
  }
  // 400 with ALLOWED_HOSTS message (set by api.js when backend returns HTML)
  if (status === 400 && msg) {
    return msg
  }
  if (status === 403 && msg && msg.includes('locked')) {
    return 'ကြိုးစားမှု အရေအတွက် များလွန်းပါသည်။ ခဏစောင့်ပြီး ထပ်ကြိုးစားပါ။'
  }
  if (status === 401) {
    if (msg && (msg.includes('No active account') || msg.includes('Invalid') || msg.includes('credentials'))) {
      return 'ဤအကောင့်မရှိပါ သို့မဟုတ် စကားဝှက်မှားနေပါသည်။ စာရင်းမသွင်းရသေးရင် အောက်က စာရင်းသွင်းရန် နှိပ်ပါ။'
    }
    return 'ဖုန်းနံပါတ်/အီးမေးလ် သို့မဟုတ် စကားဝှက် မှားယွင်းနေပါသည်။'
  }
  return 'ဝင်ရောက်၍မရပါ။ ထပ်ကြိုးစားပါ။'
}

const handleLogin = async () => {
  loading.value = true
  error.value = ''

  try {
    const success = await authStore.login(login.value, password.value)
    if (success) {
      router.push('/setup-wizard')
    }
  } catch (err) {
    error.value = getLoginErrorMessage(err)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-loyverse { background: var(--color-bg); }
.login-logo { width: 96px; height: 96px; object-fit: contain; }
.login-input {
  min-height: 48px;
  font-size: 1rem;
  padding: 0.625rem 1rem;
  border: 1px solid var(--color-border);
  border-radius: 10px;
}
.login-input::placeholder { color: var(--color-text-subtle); }
</style>
