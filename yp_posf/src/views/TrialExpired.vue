<template>
  <div class="min-h-screen flex items-center justify-center bg-[#F5F5F5] px-4 py-8 auth-page">
    <div class="auth-card max-w-md">
      <div class="text-center mb-8">
        <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-amber-100 flex items-center justify-center">
          <svg class="w-8 h-8 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h2 class="text-2xl font-bold text-fg mb-2" style="font-family: 'Noto Sans Myanmar', sans-serif;">
          {{ t.trialExpired }}
        </h2>
        <p class="text-fg-muted text-[25px] leading-relaxed">
          {{ t.trialExpiredMessage }}
        </p>
      </div>

      <div class="rounded-[12px] bg-amber-50 border border-amber-200 p-4 text-left">
        <p class="font-semibold text-fg mb-2" style="font-family: 'Noto Sans Myanmar', sans-serif;">{{ t.contactToActivate }}</p>
        <p class="text-fg-muted text-[20px] whitespace-pre-line">{{ contactDisplay }}</p>
      </div>

      <p class="mt-6 text-center text-fg-muted text-[20px]">
        {{ t.thankYou }}
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/services/api'

// Bilingual: Myanmar + English
const t = {
  trialExpired: 'Trial Expired / သက်တမ်းကုန်ပြီး',
  trialExpiredMessage: 'Your 30-day trial has ended. To continue using POS, please contact us to activate your shop. / သင့်ဆိုင်အား ဆက်လက်အသုံးပြုရန် ဆက်သွယ်ပါ။',
  contactToActivate: 'Contact to activate / သက်တမ်းတိုးချဲ့ရန် ဆက်သွယ်ပါ',
  thankYou: 'Thank you. / ကျေးဇူးတင်ပါသည်။',
}

const route = useRoute()
const contactDisplay = ref('')

onMounted(async () => {
  // Use contact passed from router (api interceptor may put it in query) or fetch from a public endpoint
  const fromQuery = route.query?.contact
  if (fromQuery) {
    try {
      contactDisplay.value = decodeURIComponent(fromQuery)
    } catch {
      contactDisplay.value = fromQuery
    }
    return
  }
  try {
    const res = await api.get('license/status/')
    if (res.data?.trial_contact) {
      contactDisplay.value = res.data.trial_contact
      return
    }
  } catch (_) {}
  contactDisplay.value = 'Contact your administrator or the person who set up this POS.\nဤ POS ကို စီမံသူ သို့မဟုတ် အက်ဒ်မင်နှင့် ဆက်သွယ်ပါ။'
})
</script>
