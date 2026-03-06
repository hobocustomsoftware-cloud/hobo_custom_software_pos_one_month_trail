<template>
  <RouterView />
</template>

<script setup>
import { RouterView } from 'vue-router'
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useShopSettingsStore } from '@/stores/shopSettings'
import { useFeatureTogglesStore } from '@/stores/featureToggles'
import { useProductFieldSettingsStore } from '@/stores/productFieldSettings'
import { useOfflinePosStore } from '@/stores/offlinePos'
import { initToastContainer } from '@/composables/useToast'
import api from '@/services/api'
import router from '@/router'

onMounted(async () => {
  initToastContainer()
  const auth = useAuthStore()
  if (auth.token) {
    // FINAL MASTER BLUEPRINT §5: License check on app load regardless of device (PC/tablet/phone)
    try {
      const res = await api.get('license/status/')
      const status = res.data?.status
      if (status === 'expired') {
        router.push('/license-activate')
        return
      }
    } catch (e) {
      if (e.response?.status === 403 && e.response?.data?.error === 'license_expired') {
        router.push('/license-activate')
        return
      }
    }
    useShopSettingsStore().fetch()
    useFeatureTogglesStore().fetch()
    useProductFieldSettingsStore().fetch()
    useOfflinePosStore().initOfflineSync()
  } else {
    useShopSettingsStore().loaded = true
    useOfflinePosStore().initOfflineSync()
  }
})
</script>

<style>
/* Loyverse: light theme from main.css (white bg, black text). No override. */
body {
  margin: 0;
  padding: 0;
}
</style>
