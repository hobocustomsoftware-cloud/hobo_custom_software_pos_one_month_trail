<template>
  <div class="auth-page min-h-screen bg-[#f5f5f5] flex flex-col items-center justify-center p-6">
    <div v-if="loading" class="text-[#4b5563]" style="font-size: 25px;">{{ t.loading }}</div>
    <div v-else-if="done" class="text-center max-w-md">
      <h1 class="font-semibold text-[#1a1a1a] mb-2" style="font-size: 25px;">{{ t.allSet }}</h1>
      <p class="text-[#4b5563]" style="font-size: 25px;">{{ t.redirecting }}</p>
    </div>
    <div v-else class="auth-card max-w-md w-full">
      <h2 class="font-semibold text-[#1a1a1a] mb-1" style="font-size: 25px;">{{ t.setupWizard }}</h2>
      <p class="text-[#4b5563] mb-6" style="font-size: 25px;">{{ t.setupSub }}</p>
      <div class="space-y-4">
        <div>
          <label class="auth-label block mb-2" style="font-size: 25px;">{{ t.businessType }}</label>
          <select v-model="businessType" class="auth-input w-full" style="font-size: 25px; min-height: 80px;">
            <option value="pharmacy">ဆေးဆိုင် (Pharmacy)</option>
            <option value="pharmacy_clinic">ဆေးခန်းတွဲ ဆေးဆိုင် (Pharmacy + Clinic)</option>
            <option value="mobile">ဖုန်း/အီလက်ထရွန်းနစ် (Mobile / Electronics)</option>
            <option value="electronic_solar">Solar / လျှပ်စစ်ပစ္စည်း (Solar & Electrical)</option>
            <option value="hardware">အိမ်ဆောက်ပစ္စည်းဆိုင် (Hardware)</option>
            <option value="liquor">အရက်ဆိုင် (Liquor Store)</option>
            <option value="grocery">ကုန်မာဆိုင် (Grocery)</option>
            <option value="general">အထွေထွေလက်လီ (General Retail)</option>
          </select>
        </div>
        <div>
          <label class="auth-label block mb-2" style="font-size: 25px;">{{ t.currency }}</label>
          <select v-model="currency" class="auth-input w-full" style="font-size: 25px; min-height: 80px;">
            <option value="MMK">MMK (Kyat)</option>
            <option value="USD">USD</option>
            <option value="THB">THB</option>
          </select>
        </div>
      </div>
      <p class="text-[#4b5563] mt-4" style="font-size: 25px;">{{ t.setupHint }}</p>
      <p v-if="setupError" class="text-[#b91c1c] mt-3" style="font-size: 25px;">{{ setupError }}</p>
      <button type="button" :disabled="saving" class="auth-btn w-full py-3 rounded-lg font-medium text-white mt-6" style="font-size: 25px; min-height: 80px;" @click="completeSetup">
        <span v-if="saving">{{ t.saving }}</span>
        <span v-else>{{ t.completeSetup }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getLoginPath } from '@/router'
import { useShopSettingsStore } from '@/stores/shopSettings'
import { useLocaleStore } from '@/stores/locale'

const router = useRouter()
const locale = useLocaleStore()
const setupLabels = {
  en: { loading: 'Loading...', allSet: 'All set', redirecting: 'Redirecting to dashboard...', setupWizard: 'Setup Wizard', setupSub: 'Choose your business type. We\'ll set up the right units for your products.', businessType: 'Business Type', currency: 'Currency', setupHint: 'E.g. Pharmacy will add units: Tablet, Strip, Bottle, Box.', saving: 'Saving...', completeSetup: 'Complete setup & go to Dashboard' },
  mm: { loading: 'ဖွင့်နေပါတယ်...', allSet: 'ပြီးပါပြီ', redirecting: 'ဒက်ရှ်ဘုတ်သို့ သွားနေပါတယ်...', setupWizard: 'ပထမဆုံးချိန်ညှိချက်', setupSub: 'လုပ်ငန်းအမျိုးအစားရွေးပါ။ ပစ္စည်းယူနစ်များ အလိုအလျောက်သတ်မှတ်မည်။', businessType: 'လုပ်ငန်းအမျိုးအစား', currency: 'ငွေကြေး', setupHint: 'ဥပမာ Pharmacy ရွေးရင် Tablet, Strip, Bottle, Box ထည့်ပေးမယ်။', saving: 'သိမ်းနေပါတယ်...', completeSetup: 'ပြီးပါပြီ ဒက်ရှ်ဘုတ်သို့သွားမည်' },
}
const t = computed(() => setupLabels[locale.lang])
const shopStore = useShopSettingsStore()
const loading = ref(true)
const saving = ref(false)
const done = ref(false)
const setupError = ref('')
const businessType = ref('pharmacy')
const currency = ref('MMK')

onMounted(async () => {
  try {
    const data = await shopStore.fetch()
    if (data && data.setup_wizard_done) {
      router.replace('/')
      return
    }
  } finally {
    loading.value = false
  }
})

async function completeSetup() {
  saving.value = true
  setupError.value = ''
  try {
    await shopStore.update({
      business_category: businessType.value,
      currency: currency.value,
      setup_wizard_done: true,
    })
    done.value = true
    setTimeout(() => router.replace('/'), 800)
  } catch (e) {
    saving.value = false
    const status = e.response?.status
    const detail = e.response?.data?.detail
    if (status === 403) {
      setupError.value = typeof detail === 'string' ? detail : 'Only the owner can update shop settings. Please sign in as owner.'
    } else if (status === 401) {
      setupError.value = 'Session expired. Please sign in again.'
      setTimeout(() => router.replace(getLoginPath()), 1500)
    } else {
      setupError.value = e.response?.data?.detail || 'Failed to save. Try again.'
    }
  }
}
</script>
