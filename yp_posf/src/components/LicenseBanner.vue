<template>
  <div
    v-if="showBanner"
    class="flex items-center justify-between gap-4 px-4 py-2.5 text-sm"
    :class="bannerClass"
  >
    <div class="flex items-center gap-3">
      <span class="font-bold">{{ bannerText }}</span>
      <span v-if="daysRemaining != null && !bannerText.includes(String(daysRemaining))" class="opacity-90">
        {{ daysRemaining }} ရက် ကျန်ပါသေးသည်။
      </span>
    </div>
    <RouterLink
      to="/license-activate"
      class="shrink-0 px-4 py-1.5 rounded-lg font-bold bg-white/20 hover:bg-white/30 transition"
    >
      License Activate လုပ်ပါ
    </RouterLink>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/services/api'

const route = useRoute()
const licenseStatus = ref(null)

const showBanner = computed(() => {
  if (!licenseStatus.value) return false
  if (route.path === '/license-activate') return false
  return ['trial', 'grace'].includes(licenseStatus.value.status)
})

const daysRemaining = computed(() => licenseStatus.value?.days_remaining ?? null)

const bannerClass = computed(() => {
  const s = licenseStatus.value?.status
  if (s === 'grace') return 'bg-amber-600 text-white'
  return 'bg-amber-500 text-white'
})

const bannerText = computed(() => {
  const s = licenseStatus.value?.status
  const days = licenseStatus.value?.days_remaining
  if (s === 'trial') {
    if (days != null) return `အစမ်းတစ်လ — ${days} ရက်ပဲ ကျန်ပါတော့တယ်။`
    return 'အစမ်းတစ်လ သုံးနေပါသည်။'
  }
  if (s === 'grace') return 'အစမ်းကုန်ပြီး Grace period ထဲရှိပါသည်။'
  return 'License Activate လုပ်ပါ။'
})

onMounted(async () => {
  try {
    const res = await api.get('license/status/')
    licenseStatus.value = res.data
  } catch {
    licenseStatus.value = null
  }
})
</script>
