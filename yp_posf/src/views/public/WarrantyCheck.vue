<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-amber-900/20 flex items-center justify-center p-4">
    <div class="w-full max-w-lg">
      <div class="bg-white/95 backdrop-blur-xl rounded-3xl shadow-2xl shadow-slate-900/20 border border-white/20 overflow-hidden">
        <div class="bg-gradient-to-r from-amber-500 to-amber-600 px-8 py-6">
          <h1 class="text-xl font-black text-white tracking-tight flex items-center gap-2">
            <Shield class="w-6 h-6" />
            အာမခံချက် စစ်ဆေးမှု
          </h1>
          <p class="text-amber-100 text-sm mt-1">Serial Number ဖြင့် Warranty အခြေအနေ စစ်ဆေးပါ</p>
        </div>

        <div class="p-8">
          <form @submit.prevent="search" class="space-y-5">
            <div>
              <label class="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">Serial Number</label>
              <input
                v-model="serialNumber"
                type="text"
                placeholder="ဥပမာ - SN123456789"
                class="w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-amber-400/50 focus:border-amber-400 outline-none transition-all"
              />
            </div>
            <button
              type="submit"
              :disabled="loading"
              class="w-full py-3.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 text-white font-bold shadow-lg shadow-amber-500/30 hover:shadow-amber-500/40 transition-all disabled:opacity-70 flex items-center justify-center gap-2"
            >
              <Search v-if="!loading" class="w-5 h-5" />
              <Loader2 v-else class="w-5 h-5 animate-spin" />
              {{ loading ? 'စစ်ဆေးနေပါသည်...' : 'စစ်ဆေးရန်' }}
            </button>
          </form>

          <div v-if="result" class="mt-6 rounded-2xl border overflow-hidden" :class="result.found && result.is_warranty_active ? 'border-emerald-200 bg-emerald-50/50' : result.found ? 'border-amber-200 bg-amber-50/50' : 'border-rose-200 bg-rose-50/50'">
            <div v-if="result.found && result.is_warranty_active" class="p-6 space-y-4">
              <div class="flex items-center gap-2 text-emerald-700 font-bold">
                <CheckCircle class="w-5 h-5" /> အာမခံချက် သက်တမ်းရှိပါသည်
              </div>
              <table class="w-full text-sm">
                <tr><td class="py-2 text-slate-500 font-medium w-36">Serial No.</td><td class="font-bold text-slate-800">{{ result.serial_number }}</td></tr>
                <tr><td class="py-2 text-slate-500 font-medium">ပစ္စည်းအမည်</td><td class="font-bold text-slate-800">{{ result.product_name || '-' }}</td></tr>
                <tr><td class="py-2 text-slate-500 font-medium">စတင်ရက်</td><td class="font-medium">{{ result.warranty_start_date || '-' }}</td></tr>
                <tr><td class="py-2 text-slate-500 font-medium">ကုန်ဆုံးရက်</td><td class="font-medium">{{ result.warranty_end_date || '-' }}</td></tr>
              </table>
            </div>
            <div v-else-if="result.found" class="p-6 space-y-4">
              <div class="flex items-center gap-2 text-amber-700 font-bold">
                <AlertCircle class="w-5 h-5" /> အာမခံချက် ကုန်ဆုံးပြီး
              </div>
              <table class="w-full text-sm">
                <tr><td class="py-2 text-slate-500 font-medium w-36">Serial No.</td><td class="font-bold text-slate-800">{{ result.serial_number }}</td></tr>
                <tr><td class="py-2 text-slate-500 font-medium">ပစ္စည်းအမည်</td><td class="font-bold text-slate-800">{{ result.product_name || '-' }}</td></tr>
                <tr><td class="py-2 text-slate-500 font-medium">ကုန်ဆုံးရက်</td><td class="font-medium">{{ result.warranty_end_date || '-' }}</td></tr>
              </table>
            </div>
            <div v-else class="p-6">
              <div class="flex items-center gap-2 text-rose-700 font-bold">
                <XCircle class="w-5 h-5" /> {{ result.message || 'Serial Number ရှာမတွေ့ပါ။' }}
              </div>
            </div>
          </div>
        </div>
      </div>
      <RouterLink to="/" class="block mt-4 text-center text-amber-200/90 hover:text-white text-sm font-medium transition-colors">← ပြန်သွားရန်</RouterLink>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Shield, Search, CheckCircle, AlertCircle, XCircle, Loader2 } from 'lucide-vue-next'
import api from '@/services/api'

const serialNumber = ref('')
const loading = ref(false)
const result = ref(null)

const search = async () => {
  if (!serialNumber.value.trim()) return
  loading.value = true
  result.value = null
  try {
    const res = await api.get('warranty/check/', {
      params: { serial_number: serialNumber.value.trim() },
    })
    result.value = res.data
  } catch (e) {
    result.value = e.response?.status === 404 ? e.response.data : { found: false, message: 'အမှားတစ်ခု ဖြစ်ပေါ်ခဲ့သည်။' }
  } finally {
    loading.value = false
  }
}
</script>
