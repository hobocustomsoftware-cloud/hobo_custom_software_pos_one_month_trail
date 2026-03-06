<template>
  <div class="p-6 bg-white rounded-3xl shadow-lg border border-gray-100 max-w-2xl mx-auto">
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-black flex items-center gap-2">
        <span>{{ isInbound ? '📥' : '🔄' }}</span>
        {{ isInbound ? 'Stock Inbound' : 'Stock Transfer' }}
      </h2>
      <button
        @click="toggleMode"
        class="text-[10px] font-black uppercase bg-blue-50 text-blue-600 px-4 py-2 rounded-xl hover:bg-blue-100 transition-all border border-blue-100"
      >
        Switch to {{ isInbound ? 'Transfer' : 'Inbound' }}
      </button>
    </div>

    <div class="space-y-4">
      <div class="flex items-center justify-between gap-2">
        <label class="block text-xs font-bold text-gray-400 uppercase ml-2">Select Product</label>
        <button
          type="button"
          @click="showScanner = true"
          class="flex items-center gap-2 px-3 py-2 rounded-xl bg-blue-50 text-blue-600 hover:bg-blue-100 text-xs font-bold border border-blue-100"
        >
          <span>📷</span> Scan
        </button>
      </div>
      <select
        v-model="form.product"
        class="w-full p-4 bg-gray-50 rounded-2xl border-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="" disabled>ပစ္စည်းရွေးချယ်ပါ</option>
        <option v-for="p in products" :key="p.id" :value="p.id">
          {{ p.name }} (Stock: {{ p.total_stock || 0 }})
        </option>
      </select>

      <div class="grid grid-cols-2 gap-4">
        <div v-if="!isInbound">
          <label class="block text-xs font-bold text-gray-400 uppercase ml-2 mb-1">From</label>
          <select
            v-model="form.from_location"
            class="w-full p-4 bg-gray-50 rounded-2xl border-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="" disabled>ဘယ်နေရာမှ</option>
            <option v-for="l in locations" :key="l.id" :value="l.id">{{ l.name }}</option>
          </select>
        </div>
        <div :class="isInbound ? 'col-span-2' : ''">
          <label class="block text-xs font-bold text-gray-400 uppercase ml-2 mb-1">
            {{ isInbound ? 'Receive Into (To)' : 'To' }}
          </label>
          <select
            v-model="form.to_location"
            class="w-full p-4 bg-gray-50 rounded-2xl border-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="" disabled>ဘယ်နေရာသို့</option>
            <option v-for="l in locations" :key="l.id" :value="l.id">{{ l.name }}</option>
          </select>
        </div>
      </div>

      <label class="block text-xs font-bold text-gray-400 uppercase ml-2">
        Quantity {{ selectedProduct?.base_unit_display ? `(${selectedProduct.base_unit_display})` : '' }}
      </label>
      <div class="flex items-center gap-2">
        <input
          v-model.number="form.quantity"
          type="number"
          min="1"
          :readonly="selectedProduct?.is_serial_tracked && !isInbound"
          :placeholder="
            selectedProduct?.is_serial_tracked && !isInbound
              ? 'Serial နံပါတ်များ အရင်ရွေးပါ'
              : 'အရေအတွက်'
          "
          class="flex-1 min-w-0 p-4 bg-gray-50 rounded-2xl border-none focus:ring-2 focus:ring-blue-500"
          :class="{ 'opacity-60 bg-gray-100': selectedProduct?.is_serial_tracked && !isInbound }"
        />
        <span
          v-if="selectedProduct?.base_unit_display"
          class="shrink-0 px-3 py-2 rounded-xl bg-blue-50 text-blue-700 text-sm font-bold border border-blue-100 whitespace-nowrap"
        >
          {{ selectedProduct.base_unit_display }}
        </span>
      </div>
      <p v-if="selectedProduct?.base_unit_display" class="text-[10px] text-gray-500 mt-1 ml-2">
        အရေအတွက်ကို {{ selectedProduct.base_unit_display }} ဖြင့် ထည့်ပါ။
      </p>

      <div v-if="selectedProduct?.is_serial_tracked" class="mt-4">
        <div
          v-if="isInbound"
          class="p-4 bg-blue-50 text-blue-700 rounded-2xl border border-blue-100 flex items-start gap-3"
        >
          <span class="text-lg">ℹ️</span>
          <p class="text-xs leading-relaxed font-medium">
            Serial tracked product ဖြစ်ပါသည်။ အဝင်သွင်းသည့်အခါ Serial နံပါတ်များကို စနစ်မှ
            <strong>အရေအတွက် ({{ form.quantity }})</strong> အလိုက် အလိုအလျောက် ထုတ်ပေးပါမည်။
          </p>
        </div>

        <div v-else>
          <label class="block text-xs font-bold text-gray-400 uppercase ml-2 mb-2">
            Select Serial Numbers
          </label>
          <div
            v-if="availableSerials.length > 0"
            class="grid grid-cols-2 md:grid-cols-3 gap-2 p-4 bg-gray-50 rounded-2xl border border-dashed border-gray-300 max-h-48 overflow-y-auto"
          >
            <div v-for="sn in availableSerials" :key="sn.id" class="flex items-center gap-2">
              <input
                type="checkbox"
                :value="sn.serial_number"
                v-model="form.serial_numbers"
                @change="updateQuantityFromSerials"
                class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span class="text-sm font-medium text-gray-700">{{ sn.serial_number }}</span>
            </div>
          </div>
          <div
            v-else
            class="p-4 bg-orange-50 text-orange-600 text-[11px] rounded-2xl border border-orange-100 italic font-medium"
          >
            ⚠️ ရွေးချယ်ထားသော နေရာတွင် Serial နံပါတ်များ မရှိပါ။
          </div>
          <p class="text-[10px] text-blue-500 mt-2 font-bold uppercase ml-2">
            Selected: {{ form.serial_numbers.length }} items
          </p>
        </div>
      </div>

      <button
        @click="handleTransfer"
        :disabled="loading || isSubmitDisabled"
        class="w-full py-4 bg-blue-600 text-white font-black rounded-2xl shadow-xl hover:bg-blue-700 disabled:bg-gray-400 transition-all mt-4 uppercase tracking-widest"
      >
        {{ loading ? 'PROCESSING...' : 'CONFIRM ' + (isInbound ? 'RECEIPT' : 'TRANSFER') }}
      </button>
    </div>
  </div>

  <BarcodeScanner v-if="showScanner" :show="showScanner" @scan="handleScanFromCamera" @close="showScanner = false" />
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useToast } from '@/composables/useToast'
import BarcodeScanner from '@/components/BarcodeScanner.vue'
import api from '@/services/api'

const toast = useToast()
const emit = defineEmits(['success'])

const isInbound = ref(true)

const form = ref({
  product: '',
  from_location: '',
  to_location: '',
  quantity: 1,
  serial_numbers: [],
  notes: '',
})
const products = ref([])
const locations = ref([])
const availableSerials = ref([])
const loading = ref(false)
const showScanner = ref(false)

const selectedProduct = computed(() => products.value.find((p) => p.id === form.value.product))

// Validations for Submit button
const isSubmitDisabled = computed(() => {
  if (isInbound.value) {
    return !form.value.product || !form.value.to_location || form.value.quantity < 1
  } else {
    const baseValid = !form.value.product || !form.value.from_location || !form.value.to_location
    if (selectedProduct.value?.is_serial_tracked) {
      return baseValid || form.value.serial_numbers.length === 0
    }
    return baseValid || form.value.quantity < 1
  }
})

// Switch between Inbound and Transfer
const toggleMode = () => {
  isInbound.value = !isInbound.value
  // Reset fields that are mode-specific
  form.value.from_location = ''
  form.value.serial_numbers = []
  form.value.quantity = 1
  availableSerials.value = []
}

// Watchers to lookup serials during transfer
watch(
  [() => form.value.product, () => form.value.from_location, isInbound],
  async ([p, loc, isIn]) => {
    if (!isIn && selectedProduct.value?.is_serial_tracked && p && loc) {
      try {
        // api service က auto token injection လုပ်ပေးတယ်
        const res = await api.get('serials/lookup/', {
          params: { product: p, location: loc },
        })
        availableSerials.value = res.data
        form.value.serial_numbers = []
        form.value.quantity = 0
      } catch (err) {
        availableSerials.value = []
      }
    } else {
      availableSerials.value = []
    }
  },
)

const updateQuantityFromSerials = () => {
  if (selectedProduct.value?.is_serial_tracked && !isInbound.value) {
    form.value.quantity = form.value.serial_numbers.length
  }
}

const handleScanFromCamera = async (code) => {
  showScanner.value = false
  const q = (code || '').trim()
  if (!q) return
  try {
    const res = await api.get('products/search/', { params: { q } })
    if (res.data?.found && res.data?.product) {
      const product = res.data.product
      const existing = products.value.find((p) => p.id === product.id)
      if (existing) {
        form.value.product = product.id
        toast.success('Product selected from scan')
      } else {
        form.value.product = product.id
        products.value = [...products.value, { ...product, total_stock: product.current_stock ?? product.total_stock }]
        toast.success('Product found and selected')
      }
    } else {
      toast.error('No product found for this code')
    }
  } catch (err) {
    toast.error(err.response?.data?.error || 'Search failed')
  }
}

const fetchData = async () => {
  try {
    // api service က auto token injection လုပ်ပေးတယ်
    const [pRes, lRes] = await Promise.all([
      api.get('staff/items/'),
      api.get('locations-admin/'),
    ])
    products.value = Array.isArray(pRes.data) ? pRes.data : pRes.data.results || []
    locations.value = Array.isArray(lRes.data) ? lRes.data : lRes.data.results || []
  } catch (err) {
    console.error('Fetch error:', err)
    toast.error(err.response?.data?.error || 'Could not load products or locations')
  }
}

const handleTransfer = async () => {
  loading.value = true
  const endpoint = isInbound.value ? 'movements/inbound/' : 'movements/transfer/'
  const productId = form.value.product != null && form.value.product !== '' ? Number(form.value.product) : null
  const toId = form.value.to_location != null && form.value.to_location !== '' ? Number(form.value.to_location) : null
  const qty = Number(form.value.quantity) || 1
  if (!productId || !toId) {
    toast.error('Please select product and location')
    loading.value = false
    return
  }
  const payload = {
    product: productId,
    to_location: toId,
    quantity: qty,
    notes: form.value.notes || (isInbound.value ? 'Initial Inbound' : 'Stock Update'),
  }
  if (!isInbound.value) {
    const fromId = form.value.from_location != null && form.value.from_location !== '' ? Number(form.value.from_location) : null
    if (!fromId) {
      toast.error('Please select from location for transfer')
      loading.value = false
      return
    }
    payload.from_location = fromId
    payload.serial_numbers = Array.isArray(form.value.serial_numbers) ? form.value.serial_numbers : []
  }

  try {
    await api.post(endpoint, payload)
    toast.success('အောင်မြင်ပါသည်')
    emit('success')
  } catch (err) {
    toast.error(err.response?.data?.error || 'လုပ်ဆောင်ချက် မအောင်မြင်ပါ')
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>
