<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-amber-900/20 flex items-center justify-center p-4">
    <div class="w-full max-w-lg">
      <div class="bg-white/95 backdrop-blur-xl rounded-3xl shadow-2xl shadow-slate-900/20 border border-white/20 overflow-hidden">
        <div class="bg-gradient-to-r from-amber-500 to-amber-600 px-8 py-6">
          <h1 class="text-xl font-black text-white tracking-tight flex items-center gap-2">
            <Wrench class="w-6 h-6" />
            စက်ပြင်ခြေရာခံမှု
          </h1>
          <p class="text-amber-100 text-sm mt-1">Repair No. နှင့် ဖုန်းနံပါတ်ဖြင့် စစ်ဆေးပါ</p>
        </div>

        <div class="p-8">
          <form @submit.prevent="search" class="space-y-5">
            <div>
              <label class="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">Repair No.</label>
              <input
                v-model="repairNo"
                type="text"
                placeholder="ဥပမာ - R-2025-001"
                class="w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-amber-400/50 focus:border-amber-400 outline-none transition-all"
              />
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">ဖုန်းနံပါတ်</label>
              <input
                v-model="phone"
                type="text"
                placeholder="ဥပမာ - 09123456789"
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

          <div v-if="result" class="mt-6 rounded-2xl border overflow-hidden" :class="result.found ? 'border-emerald-200 bg-emerald-50/50' : 'border-amber-200 bg-amber-50/50'">
            <div v-if="result.found" class="p-6 space-y-4">
              <div class="flex items-center gap-2 text-emerald-700 font-bold">
                <CheckCircle class="w-5 h-5" /> ရှာတွေ့ပါပြီ
              </div>
              <table class="w-full text-sm">
                <tr><td class="py-2 text-slate-500 font-medium w-36">Repair No.</td><td class="font-bold text-slate-800">{{ result.repair_no }}</td></tr>
                <tr><td class="py-2 text-slate-500 font-medium">ပစ္စည်းအမည်</td><td class="font-bold text-slate-800">{{ result.item_name || '-' }}</td></tr>
                <tr><td class="py-2 text-slate-500 font-medium">အခြေအနေ</td><td><span :class="statusClass(result.status)" class="px-3 py-1 rounded-full text-xs font-bold">{{ result.status_display || result.status }}</span></td></tr>
                <tr><td class="py-2 text-slate-500 font-medium">လက်ခံရက်စွဲ</td><td class="font-medium">{{ result.received_date || '-' }}</td></tr>
                <tr><td class="py-2 text-slate-500 font-medium">ပြန်ပေးမည့်ရက်</td><td class="font-medium">{{ result.return_date || '-' }}</td></tr>
                <tr><td class="py-2 text-slate-500 font-medium">ခန့်မှန်းကုန်ကျစရိတ်</td><td class="font-bold">{{ result.total_estimated_cost ? result.total_estimated_cost.toLocaleString() + ' MMK' : '-' }}</td></tr>
                <tr><td class="py-2 text-slate-500 font-medium">လာယူမည့်ဆိုင်</td><td class="font-medium">{{ result.location || '-' }}</td></tr>
              </table>
            </div>
            <div v-else class="p-6">
              <div class="flex items-center gap-2 text-amber-700 font-bold">
                <AlertCircle class="w-5 h-5" /> {{ result.message || 'စက်ပြင်မှတ်တမ်း ရှာမတွေ့ပါ။' }}
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
import { ref, computed } from 'vue'
import { Wrench, Search, CheckCircle, AlertCircle, Loader2 } from 'lucide-vue-next'
import api from '@/services/api'

const repairNo = ref('')
const phone = ref('')
const loading = ref(false)
const result = ref(null)

const statusClass = (s) => {
  const st = (s || '').toLowerCase()
  if (st === 'ready') return 'bg-emerald-100 text-emerald-700'
  if (st === 'rejected') return 'bg-rose-100 text-rose-700'
  return 'bg-amber-100 text-amber-700'
}

const search = async () => {
  if (!repairNo.value.trim() || !phone.value.trim()) return
  loading.value = true
  result.value = null
  try {
    const res = await api.get('service/track/', {
      params: { repair_no: repairNo.value.trim(), phone: phone.value.trim().replace(/\s/g, '') },
    })
    result.value = res.data
  } catch (e) {
    result.value = e.response?.status === 404 ? e.response.data : { found: false, message: 'အမှားတစ်ခု ဖြစ်ပေါ်ခဲ့သည်။' }
  } finally {
    loading.value = false
  }
}
</script>
