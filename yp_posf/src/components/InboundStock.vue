<template>
  <div class="p-6 bg-white rounded-3xl shadow-lg border border-gray-100 max-w-2xl mx-auto mt-10">
    <h2 class="text-2xl font-black mb-6 flex items-center gap-2">
      <span>📥</span> အဝင်လက်ခံခြင်း (Inbound)
    </h2>

    <div class="space-y-4">
      <label class="block text-xs font-bold text-gray-400 uppercase ml-2">Select Product</label>
      <select
        v-model="form.product"
        class="w-full p-4 bg-gray-50 rounded-2xl border-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="" disabled>ပစ္စည်းရွေးချယ်ပါ</option>
        <option v-for="p in products" :key="p.id" :value="p.id">
          {{ p.name }} (လက်ရှိစတော့: {{ p.total_stock || 0 }})
        </option>
      </select>

      <label class="block text-xs font-bold text-gray-400 uppercase ml-2"
        >Receive Into (To Location)</label
      >
      <select
        v-model="form.to_location"
        class="w-full p-4 bg-gray-50 rounded-2xl border-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="" disabled>လက်ခံမည့်နေရာ (ဂိုဒေါင်/ဆိုင်) ကိုရွေးပါ</option>
        <option v-for="l in locations" :key="l.id" :value="l.id">{{ l.name }}</option>
      </select>

      <label class="block text-xs font-bold text-gray-400 uppercase ml-2">Quantity</label>
      <input
        v-model.number="form.quantity"
        type="number"
        min="1"
        placeholder="အရေအတွက်"
        class="w-full p-4 bg-gray-50 rounded-2xl border-none focus:ring-2 focus:ring-blue-500"
      />

      <div v-if="selectedProduct?.is_serial_tracked" class="mt-4">
        <label class="block text-xs font-bold text-gray-400 uppercase ml-2 mb-2"
          >Enter Serial Numbers (Comma Separated)</label
        >
        <textarea
          v-model="serialInput"
          placeholder="ဥပမာ- SN001, SN002, SN003"
          class="w-full p-4 bg-gray-50 rounded-2xl border-none focus:ring-2 focus:ring-blue-500 h-24"
        ></textarea>
        <p class="text-[10px] text-blue-500 mt-1 font-bold">
          အရေအတွက်နှင့် Serial အရေအတွက် တူရပါမည်။
        </p>
      </div>

      <button
        @click="handleInbound"
        :disabled="loading"
        class="w-full py-4 bg-green-600 text-white font-black rounded-2xl shadow-green-200 shadow-xl hover:bg-green-700 transition-all mt-4 uppercase tracking-widest"
      >
        {{ loading ? 'SAVING...' : 'CONFIRM RECEIPT' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '@/services/api'
const form = ref({
  product: '',
  to_location: '',
  from_location: null, // အဝင်ဖြစ်လို့ null ထားမယ်
  quantity: 1,
  serial_numbers: [],
  notes: 'New Stock Arrival',
})

const serialInput = ref('')
const products = ref([])
const locations = ref([])
const loading = ref(false)

// api service က auto token injection လုပ်ပေးတယ်

const selectedProduct = computed(() => products.value.find((p) => p.id === form.value.product))

const fetchData = async () => {
  // api service က auto token injection လုပ်ပေးတယ်
  const [pRes, lRes] = await Promise.all([
    api.get('staff/items/'),
    api.get('locations-admin/'),
  ])
  products.value = Array.isArray(pRes.data) ? pRes.data : (pRes.data?.results ?? [])
  locations.value = Array.isArray(lRes.data) ? lRes.data : (lRes.data?.results ?? [])
}

const handleInbound = async () => {
  // Serial ရှိရင် Array ပြောင်းမယ်
  if (selectedProduct.value?.is_serial_tracked) {
    const sns = serialInput.value
      .split(',')
      .map((s) => s.trim())
      .filter((s) => s !== '')
    if (sns.length !== form.value.quantity) {
      alert(`Serial အရေအတွက် (${sns.length}) နှင့် Quantity (${form.value.quantity}) မကိုက်ညီပါ။`)
      return
    }
    form.value.serial_numbers = sns
  }

  loading.value = true
  try {
    // api service က auto token injection လုပ်ပေးတယ်
    await api.post('movements/transfer/', form.value)
    alert('ပစ္စည်းအဝင်စာရင်းသွင်းပြီးပါပြီ!')
    // Reset Form
    form.value.product = ''
    form.value.quantity = 1
    serialInput.value = ''
    fetchData()
  } catch (err) {
    alert(err.response?.data?.error || 'အမှားအယွင်းရှိနေပါသည်')
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>
