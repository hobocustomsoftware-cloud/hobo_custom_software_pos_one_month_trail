<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-lang-toggle">
        <button type="button" class="auth-lang-btn" :class="{ active: locale.isEn }" @click="locale.setLang('en')">EN</button>
        <button type="button" class="auth-lang-btn" :class="{ active: locale.isMm }" @click="locale.setLang('mm')">မြန်မာ</button>
      </div>
      <div class="text-center mb-6">
        <img v-show="!logoError && shopLogo" :src="shopLogo" alt="Logo" class="auth-logo mx-auto mb-3 object-contain rounded-lg" @error="logoError = true" />
        <img v-show="!logoError && !shopLogo && !logoSvgFallback" :src="defaultLogo" alt="Logo" class="auth-logo mx-auto mb-3 object-contain rounded-lg" @error="logoSvgFallback = true" />
        <img v-show="!logoError && !shopLogo && logoSvgFallback" :src="fallbackLogo" alt="Logo" class="auth-logo mx-auto mb-3 object-contain rounded-lg" @error="logoError = true" />
        <span v-show="logoError" class="font-semibold text-[var(--color-primary)]">{{ shopName }}</span>
        <h2 class="font-semibold text-[#000000] mt-2">{{ t.createAccount }}</h2>
        <p class="text-[#374151] mt-1">{{ t.createAccountSub }}</p>
      </div>

      <form @submit.prevent="handleRegister" class="space-y-4">
        <div>
          <label class="auth-label block mb-1 font-medium text-[#000000]">{{ t.ownerName }}</label>
          <input v-model="form.owner_name" type="text" class="auth-input auth-input-text w-full" :placeholder="locale.isEn ? 'Owner name' : 'ပိုင်ရှင်အမည်'" required autocomplete="name" />
        </div>
        <div>
          <label class="auth-label block mb-1 font-medium text-[#000000]">{{ t.phoneNumber }}</label>
          <input v-model="form.phone_number" type="tel" class="auth-input auth-input-text w-full" :placeholder="locale.isEn ? '09xxxxxxxx or +959xxxxxxxx' : '၀၉xxxxxxxx သို့မဟုတ် +၉၅၉xxxxxxxx'" required autocomplete="tel" />
        </div>
        <div>
          <label class="auth-label block mb-1 font-medium text-[#000000]">{{ t.shopName }}</label>
          <input v-model="form.shop_name" type="text" class="auth-input auth-input-text w-full" :placeholder="locale.isEn ? 'My Shop' : 'ဆိုင်အမည်'" required autocomplete="organization" />
        </div>
        <div>
          <label class="auth-label block mb-1 font-medium text-[#000000]">{{ t.password }}</label>
          <input v-model="form.password" type="password" required minlength="6" class="auth-input auth-input-text w-full" placeholder="••••••••" />
        </div>
        <div>
          <label class="auth-label block mb-1 font-medium text-[#000000]">{{ t.confirmPassword }}</label>
          <input v-model="form.password_confirm" type="password" required class="auth-input auth-input-text w-full" placeholder="••••••••" />
        </div>
        <button type="submit" :disabled="loading" class="auth-btn w-full flex justify-center items-center gap-2">
          <span v-if="loading">{{ t.creating }}</span>
          <span v-else>{{ t.createAccountBtn }}</span>
        </button>
        <p v-if="error" class="text-[#b91c1c] text-center font-medium">{{ error }}</p>
        <p v-if="success" class="text-[#166534] text-center font-medium">{{ success }}</p>
      </form>
      <p class="text-center text-[#374151] mt-4">
        {{ t.alreadyHave }}
        <RouterLink to="/login" class="auth-link font-medium">{{ t.signInLink }}</RouterLink>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { getLoginPath } from '@/router'
import api from '@/services/api'
import { useShopSettingsStore } from '@/stores/shopSettings'
import { useLocaleStore } from '@/stores/locale'
import { authLabels } from '@/stores/locale'

const locale = useLocaleStore()
const t = computed(() => authLabels[locale.lang])

const router = useRouter()
const shopStore = useShopSettingsStore()
const base = (import.meta.env.BASE_URL || '/').replace(/\/$/, '') + '/'
const defaultLogo = base + 'logo.png'
const fallbackLogo = base + 'logo.svg'
const logoError = ref(false)
const logoSvgFallback = ref(false)
const shopLogo = computed(() => shopStore.logo_url)
const shopName = computed(() => shopStore.displayName)
const form = reactive({
  owner_name: '',
  phone_number: '',
  shop_name: '',
  password: '',
  password_confirm: '',
})
const loading = ref(false)
const error = ref('')
const success = ref('')

async function handleRegister() {
  const hasName = (form.owner_name || '').trim().length > 0
  const hasPhone = (form.phone_number || '').trim().length > 0
  const hasShop = (form.shop_name || '').trim().length > 0
  if (!hasName) {
    error.value = locale.lang === 'mm' ? 'ပိုင်ရှင်အမည် ထည့်ပါ။' : 'Owner name is required.'
    return
  }
  if (!hasPhone) {
    error.value = locale.lang === 'mm' ? 'ဖုန်းနံပါတ် ထည့်ပါ။' : 'Phone number is required.'
    return
  }
  if (!hasShop) {
    error.value = locale.lang === 'mm' ? 'ဆိုင်အမည် ထည့်ပါ။' : 'Shop name is required.'
    return
  }
  loading.value = true
  error.value = ''
  success.value = ''
  try {
    const payload = {
      owner_name: (form.owner_name || '').trim() || undefined,
      phone_number: (form.phone_number || '').trim() || undefined,
      shop_name: (form.shop_name || '').trim() || '',
      password: form.password,
      password_confirm: form.password_confirm,
    }
    const res = await api.post('core/register/', payload)
    success.value = res.data?.message || 'Account created.'
    const data = res.data
    const savedPassword = form.password
    form.owner_name = ''
    form.phone_number = ''
    form.shop_name = ''
    form.password = ''
    form.password_confirm = ''
    // Loyverse-style: first user gets tokens from register → no second login (avoids 401)
    if (data?.can_login_now && data?.access) {
      const { useAuthStore } = await import('@/stores/auth')
      const authStore = useAuthStore()
      authStore.token = data.access
      localStorage.setItem('access_token', data.access)
      if (data.refresh) localStorage.setItem('refresh_token', data.refresh)
      if (data.user) {
        authStore.user = data.user
        authStore.role = data.user.role || data.user.role_name
        localStorage.setItem('user', JSON.stringify(data.user))
        localStorage.setItem('user_role', authStore.role || '')
      }
      if (data.outlet) localStorage.setItem('outlet', JSON.stringify(data.outlet))
      router.push('/setup-wizard')
    } else if (data?.can_login_now && savedPassword) {
      const { useAuthStore } = await import('@/stores/auth')
      const authStore = useAuthStore()
      const savedLogin = (data.phone_number || '').trim()
      if (savedLogin) {
        try {
          await authStore.login(savedLogin, savedPassword)
          router.push('/setup-wizard')
        } catch {
          setTimeout(() => router.push(getLoginPath()), 2000)
        }
      } else {
        setTimeout(() => router.push(getLoginPath()), 2000)
      }
    } else {
      setTimeout(() => router.push(getLoginPath()), 2000)
    }
  } catch (e) {
    if (!e.response || e.response.status === 0 || e.code === 'ERR_NETWORK') {
      error.value = 'Cannot reach server. Start the backend.'
    } else {
      const d = e.response?.data
      const first = (arr) => (Array.isArray(arr) ? arr[0] : arr)
      if (d?.phone_number) error.value = first(d.phone_number)
      else if (d?.email) error.value = first(d.email)
      else if (d?.shop_name) error.value = first(d.shop_name)
      else if (d?.password) error.value = first(d.password)
      else if (d?.password_confirm) error.value = first(d.password_confirm)
      else if (d?.detail) error.value = typeof d.detail === 'string' ? d.detail : first(d.detail)
      else if (typeof d === 'object' && d !== null && !Array.isArray(d)) {
        const msg = Object.values(d).flat().find(Boolean)
        error.value = msg ? (Array.isArray(msg) ? msg[0] : msg) : 'Registration failed. Check your input.'
      } else error.value = 'Registration failed. Try again.'
    }
  } finally {
    loading.value = false
  }
}
</script>
