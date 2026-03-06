<template>
  <div class="relative font-sans text-white/90">
    <div
      :class="{ 'blur-sm pointer-events-none': isPanelOpen || isInboundOpen || isTransferOpen }"
      class="space-y-6 max-w-[1600px] mx-auto transition-all"
    >
      <div class="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <h1 class="text-2xl md:text-3xl font-black text-white tracking-tight">
            INVENTORY CONTROL
          </h1>
          <div class="flex items-center gap-3 mt-2">
            <span
              class="flex items-center gap-1.5 px-3 py-1 bg-white/10 text-white/80 rounded-full text-[10px] font-black uppercase tracking-widest border border-white/20"
            >
              <span class="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse"></span>
              {{ locations.length }} Active Nodes
            </span>
          </div>
        </div>
        <div class="flex gap-3">
          <button
            @click="openInboundModal"
            class="px-6 py-3 bg-white/10 border border-white/20 rounded-2xl text-[11px] font-black text-white/90 hover:bg-white/20 flex items-center gap-2 transition-all duration-300"
          >
            <Plus class="w-4 h-4" /> INBOUND ENTRY
          </button>
          <button
            @click="fetchData"
            class="p-3 bg-white/20 text-white rounded-2xl hover:bg-white/30 transition-all"
          >
            <RotateCw :class="{ 'animate-spin': isLoading }" class="w-5 h-5" />
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div
          v-for="(stat, idx) in statsData"
          :key="idx"
          class="glass-card p-6"
        >
          <div class="flex justify-between items-start mb-4">
            <div class="p-3 rounded-2xl bg-white/10 border border-white/20">
              <component :is="stat.icon" class="w-5 h-5 text-white/80" />
            </div>
            <p class="text-[10px] font-black text-white/80 uppercase tracking-widest">
              {{ stat.label }}
            </p>
          </div>
          <h3 :class="['text-2xl font-black tracking-tighter', stat.isAlert ? 'text-rose-300' : 'text-white']">
            {{ stat.value }}
          </h3>
          <p class="text-[10px] font-bold text-white/70 mt-1">{{ stat.desc }}</p>
        </div>
      </div>

      <div class="relative">
        <Search class="w-4 h-4 absolute left-6 top-1/2 -translate-y-1/2 text-white/40" />
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Scan barcode or search SKU..."
          class="w-full pl-16 pr-6 py-5 glass-input text-sm font-bold"
        />
      </div>

      <div class="glass-card rounded-[2rem] overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-left border-separate border-spacing-0">
            <thead>
              <tr class="text-[10px] font-black text-white/80 uppercase tracking-[0.2em] bg-white/10">
                <th class="px-6 md:px-8 py-5">Product Details</th>
                <th class="px-6 md:px-8 py-5 text-center">In Stock</th>
                <th class="px-6 md:px-8 py-5 text-right">Retail Price</th>
                <th class="px-6 md:px-8 py-5 text-center">Quick Actions</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-white/10">
              <tr
                v-for="prod in productList"
                :key="prod.id"
                class="group hover:bg-white/5 transition-all"
              >
                <td class="px-6 md:px-8 py-5">
                  <div class="flex items-center gap-4">
                    <div class="w-12 h-12 bg-white/10 rounded-2xl flex items-center justify-center border border-white/20">
                      <Box class="w-6 h-6 text-white/50" />
                    </div>
                    <div>
                      <p class="text-[14px] font-black text-white/90 leading-tight">
                        {{ prod.name }}
                      </p>
                      <p class="text-[10px] text-white/70 font-bold mt-1">#{{ prod.sku }}</p>
                    </div>
                  </div>
                </td>
                <td class="px-6 md:px-8 py-5 text-center">
                  <span
                    :class="[
                      'text-[14px] font-black',
                      (prod.current_stock ?? prod.total_stock ?? 0) <= 5 ? 'text-rose-300' : 'text-white/90',
                    ]"
                    >{{ prod.current_stock ?? prod.total_stock ?? 0 }}</span
                  >
                </td>
                <td class="px-6 md:px-8 py-5 text-right font-black text-white/90">
                  {{ formatCurrency(prod.retail_price) }}
                </td>
                <td class="px-6 md:px-8 py-5 text-center space-x-2">
                  <button
                    @click="openTransferModal(prod)"
                    class="p-2 hover:bg-white/10 text-white/80 rounded-xl transition-all"
                    title="Transfer Stock"
                  >
                    <ArrowRightLeft class="w-5 h-5" />
                  </button>
                  <button
                    @click="openDetails(prod)"
                    class="p-2 hover:bg-white/10 text-white/50 rounded-xl transition-all"
                  >
                    <MoreVertical class="w-5 h-5" />
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div
          v-if="productsTotalCount > 0"
          class="flex flex-wrap items-center justify-between gap-4 p-4 border-t border-white/10"
        >
          <p class="text-sm text-white/60">
            Showing {{ (productsPage - 1) * productsPageSize + 1 }}–{{ Math.min(productsPage * productsPageSize, productsTotalCount) }} of {{ productsTotalCount }}
          </p>
          <div class="flex items-center gap-2">
            <button
              :disabled="productsPage <= 1 || isLoading"
              class="px-4 py-2 rounded-xl border border-white/20 text-white/80 hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed transition"
              @click="setPage(productsPage - 1)"
            >
              Previous
            </button>
            <span class="px-3 py-2 text-sm font-bold text-white/80">
              Page {{ productsPage }} of {{ productsTotalPages }}
            </span>
            <button
              :disabled="productsPage >= productsTotalPages || isLoading"
              class="px-4 py-2 rounded-xl border border-white/20 text-white/80 hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed transition"
              @click="setPage(productsPage + 1)"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="isInboundOpen"
      class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
    >
      <div class="w-full max-w-md rounded-[2rem] p-8 shadow-glow border border-white/20 bg-white/10 backdrop-blur-2xl space-y-6">
        <div class="flex justify-between items-center">
          <h2 class="text-xl font-black text-white">STOCK INBOUND</h2>
          <button @click="isInboundOpen = false" class="p-2 hover:bg-white/10 rounded-xl"><X class="w-6 h-6 text-white/60" /></button>
        </div>
        <div class="space-y-4">
          <div class="space-y-1">
            <label class="glass-label ml-2">Product</label>
            <select v-model="form.product" class="w-full p-4 glass-input text-sm font-bold">
              <option v-for="p in productList" :key="p.id" :value="p.id">{{ p.name }}</option>
            </select>
          </div>
          <div class="space-y-1">
            <label class="glass-label ml-2">Destination Location</label>
            <select v-model="form.to_location" class="w-full p-4 glass-input text-sm font-bold">
              <option v-for="l in locations" :key="l.id" :value="l.id">{{ l.name }}</option>
            </select>
          </div>
          <div class="space-y-1">
            <label class="glass-label ml-2">Quantity</label>
            <div class="flex flex-wrap items-center gap-2">
              <input v-model="form.quantity" type="number" min="0" step="1" class="flex-1 min-w-[80px] p-4 glass-input text-sm font-bold" />
              <select v-if="inboundUnitOptions.length" v-model="form.unit" class="min-w-[140px] p-4 glass-input text-sm font-bold rounded-xl">
                <option v-for="u in inboundUnitOptions" :key="u.id" :value="u.id">{{ u.label }}</option>
              </select>
              <span v-else-if="inboundSelectedProduct?.base_unit_display" class="shrink-0 px-3 py-2 rounded-xl bg-white/20 text-white text-sm font-bold border border-white/30">{{ inboundSelectedProduct.base_unit_display }}</span>
            </div>
            <p v-if="inboundSelectedProduct && inboundUnitOptions.length" class="text-xs text-white/60 mt-1">ယူနစ်ရွေးပါ။ ရွေးထားတဲ့ယူနစ်အတိုင်း ပမာဏ ထည့်ပါ။</p>
          </div>
        </div>
        <button
          @click="handleInbound"
          class="w-full py-4 bg-white/20 hover:bg-white/30 text-white rounded-2xl font-black border border-white/20 transition-all"
        >
          CONFIRM ENTRY
        </button>
      </div>
    </div>

    <div
      v-if="isTransferOpen"
      class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
    >
      <div class="w-full max-w-md rounded-[2rem] p-8 shadow-glow border border-white/20 bg-white/10 backdrop-blur-2xl space-y-6">
        <div class="flex justify-between items-center">
          <h2 class="text-xl font-black text-white">STOCK TRANSFER</h2>
          <button @click="isTransferOpen = false" class="p-2 hover:bg-white/10 rounded-xl"><X class="w-6 h-6 text-white/60" /></button>
        </div>
        <div class="space-y-4">
          <p class="text-center font-bold text-white/80 bg-white/10 py-2 rounded-xl text-sm border border-white/20">
            {{ selectedItem.name }}
          </p>
          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-1">
              <label class="glass-label ml-2">From</label>
              <select v-model="form.from_location" class="w-full p-4 glass-input text-sm font-bold">
                <option v-for="l in locations" :key="l.id" :value="l.id">{{ l.name }}</option>
              </select>
            </div>
            <div class="space-y-1">
              <label class="glass-label ml-2">To</label>
              <select v-model="form.to_location" class="w-full p-4 glass-input text-sm font-bold">
                <option v-for="l in locations" :key="l.id" :value="l.id">{{ l.name }}</option>
              </select>
            </div>
          </div>
          <div class="space-y-1">
            <label class="glass-label ml-2">Quantity</label>
            <div class="flex flex-wrap items-center gap-2">
              <input v-model="form.quantity" type="number" min="0" step="1" class="flex-1 min-w-[80px] p-4 glass-input text-sm font-bold" />
              <select v-if="transferUnitOptions.length" v-model="form.unit" class="min-w-[140px] p-4 glass-input text-sm font-bold rounded-xl">
                <option v-for="u in transferUnitOptions" :key="u.id" :value="u.id">{{ u.label }}</option>
              </select>
              <span v-else-if="selectedItem?.base_unit_display" class="shrink-0 px-3 py-2 rounded-xl bg-white/20 text-white text-sm font-bold border border-white/30">{{ selectedItem.base_unit_display }}</span>
            </div>
            <p v-if="selectedItem && transferUnitOptions.length" class="text-xs text-white/60 mt-1">ယူနစ်ရွေးပါ။ ရွေးထားတဲ့ယူနစ်အတိုင်း ပမာဏ ထည့်ပါ။</p>
          </div>
        </div>
        <button
          @click="handleTransfer"
          class="w-full py-4 bg-white/20 hover:bg-white/30 text-white rounded-2xl font-black border border-white/20 transition-all"
        >
          EXECUTE TRANSFER
        </button>
      </div>
    </div>

    <transition name="panel">
      <div
        v-if="isPanelOpen"
        class="fixed inset-y-0 right-0 w-full md:w-[500px] bg-white/10 backdrop-blur-2xl border-l border-white/20 shadow-glow z-50 flex flex-col"
      >
        <div class="p-8 border-b border-white/20 flex justify-between items-center">
          <h2 class="text-xl font-black text-white tracking-tight">Product Specs</h2>
          <button @click="isPanelOpen = false" class="p-2 hover:bg-white/10 text-white/60 rounded-xl transition-all">
            <X class="w-6 h-6" />
          </button>
        </div>
        <div class="flex-1 overflow-y-auto p-8 space-y-6">
          <div class="p-6 rounded-[2rem] border border-white/20 bg-white/5">
            <p class="glass-label mb-2">Current Total Stock</p>
            <p class="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-br from-white to-white/50">
              {{ selectedItem.stock }} <span class="text-sm font-bold text-white/40">UNITS</span>
            </p>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <button
              @click="openTransferModal(selectedItem)"
              class="p-4 bg-white/20 hover:bg-white/30 text-white rounded-2xl font-black text-xs border border-white/20"
            >
              TRANSFER
            </button>
            <button class="p-4 bg-white/10 border border-white/20 text-white/80 rounded-2xl font-black text-xs hover:bg-white/20">
              EDIT INFO
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import api from '@/services/api'
import { useToast } from '@/composables/useToast'
import {
  Plus,
  Search,
  RotateCw,
  Box,
  X,
  TrendingUp,
  AlertCircle,
  MapPin,
  MoreVertical,
  ArrowRightLeft,
  Download,
} from 'lucide-vue-next'

const toast = useToast()

// --- State ---
const products = ref([])
const productsPage = ref(1)
const productsPageSize = ref(20)
const productsTotalCount = ref(0)
const locations = ref([])
const categories = ref([])
const lowStockItems = ref([])
const summary = ref({ total_value: 0 })
const dailySummary = ref({})

const isLoading = ref(false)
const searchQuery = ref('')
const searchDebounce = ref(null)
const isPanelOpen = ref(false)
const isInboundOpen = ref(false)
const isTransferOpen = ref(false)
const selectedItem = ref({})

const form = ref({
  product: '',
  location: '',
  from_location: '',
  to_location: '',
  quantity: 1,
  remarks: 'Admin Entry',
})

// --- Logic ---
const formatCurrency = (v) =>
  new Intl.NumberFormat('en-MM', {
    style: 'currency',
    currency: 'MMK',
    maximumFractionDigits: 0,
  }).format(v || 0)

const statsData = computed(() => [
  {
    label: 'Total Value',
    value: formatCurrency(summary.value.total_value),
    desc: 'Stock valuation',
    icon: TrendingUp,
    bgColor: 'bg-emerald-50',
    textColor: 'text-emerald-600',
  },
  {
    label: 'Low Stock',
    value: Array.isArray(lowStockItems.value) ? lowStockItems.value.length : 0,
    desc: 'Critical alerts',
    icon: AlertCircle,
    bgColor: 'bg-rose-50',
    textColor: 'text-rose-600',
    isAlert: Array.isArray(lowStockItems.value) && lowStockItems.value.length > 0,
  },
  {
    label: 'Network',
    value: Array.isArray(locations.value) ? locations.value.length : 0,
    desc: 'Active warehouses',
    icon: MapPin,
    bgColor: 'bg-blue-50',
    textColor: 'text-blue-600',
  },
  {
    label: 'Movements',
    value: dailySummary.value.total_sales_count || 0,
    desc: 'Logged today',
    icon: Box,
    bgColor: 'bg-amber-50',
    textColor: 'text-amber-600',
  },
])

const productList = computed(() => Array.isArray(products.value) ? products.value : [])

const inboundSelectedProduct = computed(() => {
  const id = form.value.product
  if (!id) return null
  return productList.value.find((p) => p.id === id) || null
})

/** Unit options for inbound: base_unit + purchase_unit (if any) of selected product */
const inboundUnitOptions = computed(() => {
  const p = inboundSelectedProduct.value
  if (!p) return []
  const opts = []
  if (p.base_unit != null && p.base_unit_display) opts.push({ id: p.base_unit, label: p.base_unit_display })
  if (p.purchase_unit != null && p.purchase_unit_display && String(p.purchase_unit) !== String(p.base_unit)) opts.push({ id: p.purchase_unit, label: p.purchase_unit_display })
  if (opts.length === 0 && p.base_unit_display) opts.push({ id: p.base_unit ?? '', label: p.base_unit_display })
  return opts
})

/** Unit options for transfer: from selectedItem (same structure) */
const transferUnitOptions = computed(() => {
  const p = selectedItem.value
  if (!p) return []
  const opts = []
  if (p.base_unit != null && p.base_unit_display) opts.push({ id: p.base_unit, label: p.base_unit_display })
  if (p.purchase_unit != null && p.purchase_unit_display && String(p.purchase_unit) !== String(p.base_unit)) opts.push({ id: p.purchase_unit, label: p.purchase_unit_display })
  if (opts.length === 0 && p.base_unit_display) opts.push({ id: p.base_unit ?? '', label: p.base_unit_display })
  return opts
})

const productsTotalPages = computed(() =>
  Math.max(1, Math.ceil(productsTotalCount.value / productsPageSize.value))
)

/** Fetch one page of products from API (server-side pagination + search) */
const fetchProducts = async () => {
  const token = localStorage.getItem('access_token')
  const config = { headers: { Authorization: `Bearer ${token}` } }
  const params = { page: productsPage.value, page_size: productsPageSize.value }
  if (searchQuery.value?.trim()) params.search = searchQuery.value.trim()
  try {
    const res = await axios.get('/api/products-admin/', { ...config, params })
    products.value = Array.isArray(res.data.results) ? res.data.results : (res.data.results ?? [])
    productsTotalCount.value = res.data.count ?? products.value.length
  } catch (e) {
    console.error(e)
    products.value = []
  }
}

/** Fetch locations, categories, low-stock, summary (no products) */
const fetchOtherData = async () => {
  const token = localStorage.getItem('access_token')
  const config = { headers: { Authorization: `Bearer ${token}` } }
  try {
    const [l, cat, low, full, daily] = await Promise.all([
      axios.get('/api/locations/', config),
      axios.get('/api/categories/', config),
      axios.get('/api/admin/report/low-stock/', config),
      axios.get('/api/admin/report/full-inventory/', config),
      axios.get('/api/admin/report/daily-summary/', config),
    ])
    locations.value = Array.isArray(l.data) ? l.data : (l.data?.results ?? [])
    categories.value = Array.isArray(cat.data) ? cat.data : (cat.data?.results ?? [])
    lowStockItems.value = Array.isArray(low.data) ? low.data : (low.data?.results ?? [])
    summary.value = full.data && typeof full.data === 'object' ? full.data : { total_value: 0 }
    dailySummary.value = daily.data && typeof daily.data === 'object' ? daily.data : {}
  } catch (e) {
    console.error(e)
  }
}

const fetchData = async () => {
  isLoading.value = true
  try {
    await Promise.all([fetchProducts(), fetchOtherData()])
  } finally {
    isLoading.value = false
  }
}

const setPage = (p) => {
  if (p >= 1 && p <= productsTotalPages.value) {
    productsPage.value = p
    fetchProducts()
  }
}

watch(searchQuery, () => {
  if (searchDebounce.value) clearTimeout(searchDebounce.value)
  searchDebounce.value = setTimeout(() => {
    productsPage.value = 1
    fetchProducts()
  }, 350)
})

watch(inboundUnitOptions, (opts) => {
  if (opts.length > 0 && !opts.some((o) => String(o.id) === String(form.value.unit))) form.value.unit = opts[0].id
}, { immediate: true })

// --- Actions ---
const openInboundModal = () => {
  form.value = { product: '', to_location: '', quantity: 1, unit: '', remarks: 'Inbound Entry' }
  isInboundOpen.value = true
}

const openTransferModal = (item) => {
  selectedItem.value = item
  const baseId = item.base_unit || (item.base_unit_display ? '' : '')
  form.value = {
    product: item.id,
    from_location: '',
    to_location: '',
    quantity: 1,
    unit: baseId,
    remarks: 'Stock Transfer',
  }
  isTransferOpen.value = true
}

const handleInbound = async () => {
  const productId = form.value.product && Number(form.value.product)
  const toLocationId = form.value.to_location && Number(form.value.to_location)
  const qty = Number(form.value.quantity) || 1
  if (!productId || !toLocationId) {
    toast.error('Please select product and location')
    return
  }
  try {
    const payload = {
      product: productId,
      to_location: toLocationId,
      quantity: qty,
      notes: form.value.remarks || 'Inbound Entry',
    }
    if (form.value.unit) payload.unit = form.value.unit
    await api.post('movements/inbound/', payload)
    toast.success('Stock Added Successfully')
    isInboundOpen.value = false
    fetchData()
  } catch (e) {
    toast.error(e.response?.data?.error || 'Error adding stock')
  }
}

const handleTransfer = async () => {
  const productId = form.value.product && Number(form.value.product)
  const fromId = form.value.from_location && Number(form.value.from_location)
  const toId = form.value.to_location && Number(form.value.to_location)
  const qty = Number(form.value.quantity) || 1
  if (!productId || !fromId || !toId) {
    toast.error('Please select product, from location, and to location')
    return
  }
  try {
    const payload = {
      product: productId,
      from_location: fromId,
      to_location: toId,
      quantity: qty,
      notes: form.value.remarks || 'Stock Transfer',
    }
    if (form.value.unit) payload.unit = form.value.unit
    await api.post('movements/transfer/', payload)
    toast.success('Stock Transferred Successfully')
    isTransferOpen.value = false
    fetchData()
  } catch (e) {
    toast.error(e.response?.data?.error || 'Error transferring stock')
  }
}

const openDetails = (item) => {
  selectedItem.value = item
  isPanelOpen.value = true
}

onMounted(fetchData)
</script>

<style scoped>
.panel-enter-active,
.panel-leave-active {
  transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}
.panel-enter-from,
.panel-leave-to {
  transform: translateX(100%);
}
input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
</style>
