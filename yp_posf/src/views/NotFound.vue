<template>
  <div class="min-h-screen flex flex-col items-center justify-center p-6 bg-[var(--color-bg)] text-[var(--color-fg)]">
    <div class="text-center max-w-md">
      <p class="text-8xl font-black text-[var(--color-fg-muted)] select-none">404</p>
      <h1 class="text-xl font-bold mt-4">{{ isMm ? 'စာမျက်နှာ မတွေ့ပါ' : 'Page not found' }}</h1>
      <p class="text-sm text-[var(--color-fg-muted)] mt-2">
        {{ isMm ? 'သင်ရှာသော လင့်ခ်သည် မရှိသို့မဟုတ် ပြောင်းသွားပြီဖြစ်နိုင်ပါသည်။' : 'The page you are looking for does not exist or has been moved.' }}
      </p>
      <div class="mt-8 flex flex-wrap gap-3 justify-center">
        <RouterLink
          to="/"
          class="px-5 py-2.5 rounded-xl font-bold bg-[var(--loyverse-blue)] text-white hover:opacity-90 transition"
        >
          {{ isMm ? 'ပင်မစာမျက်နှာသို့' : 'Go to home' }}
        </RouterLink>
        <RouterLink
          to="/sales/pos"
          class="px-5 py-2.5 rounded-xl font-bold border-2 border-[var(--color-border)] hover:bg-[var(--color-bg-card)] transition"
        >
          {{ isMm ? 'POS' : 'POS' }}
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { useLocaleStore } from '@/stores/locale'

const locale = useLocaleStore()
const isMm = computed(() => locale.lang === 'mm')
</script>
