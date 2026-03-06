<template>
  <div class="max-w-6xl mx-auto space-y-6">
    <div class="flex flex-wrap items-center justify-between gap-4">
      <h1 class="text-xl font-semibold text-[var(--color-text)]">Purchase Orders</h1>
      <button
        type="button"
        @click="openCreate"
        :disabled="outlets.length === 0"
        class="btn-primary px-4 py-2.5 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Plus class="w-4 h-4" /> New Purchase
      </button>
    </div>

    <div class="bg-white rounded-xl shadow-sm overflow-hidden min-h-[200px]">
      <div v-if="loading" class="p-12 text-center text-[var(--color-text-muted)]">Loading...</div>
      <div v-else-if="outlets.length === 0" class="p-12 text-center">
        <p class="text-[var(--color-text-muted)] font-medium mb-2">ပစ္စည်းဝယ်ယူမည့် ဆိုင်ခွဲ (Outlet) မရှိသေးပါ။</p>
        <p class="text-sm text-[var(--color-text-muted)] mb-4">Shop Locations မှ ဆိုင်ခွဲ ဖန်တီးပြီးမှ Purchase Order ထည့်လို့ရပါမယ်။</p>
        <RouterLink to="/shop-locations" class="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl font-medium text-white bg-[var(--color-primary)] hover:opacity-90">
          Shop Locations သို့သွားမည်
        </RouterLink>
      </div>
      <div v-else-if="purchases.length === 0" class="p-12 text-center text-[var(--color-text-muted)]">
        Purchase orders မရှိသေးပါ။ New Purchase နှိပ်ပြီး ထည့်ပါ။
      </div>
      <div v-else class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-[var(--color-bg-light)]">
            <tr>
              <th class="p-3 text-left text-sm font-semibold text-[var(--color-text)]">Ref</th>
              <th class="p-3 text-left text-sm font-semibold text-[var(--color-text)]">Outlet</th>
              <th class="p-3 text-left text-sm font-semibold text-[var(--color-text)]">Date</th>
              <th class="p-3 text-left text-sm font-semibold text-[var(--color-text)]">Lines</th>
              <th class="p-3 text-left text-sm font-semibold text-[var(--color-text)]">By</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[var(--color-border)]">
            <tr
              v-for="p in purchases"
              :key="p.id"
              class="hover:bg-[var(--color-bg-light)] transition-colors"
            >
              <td class="p-3 font-medium text-[var(--color-text)]">{{ p.reference || '–' }}</td>
              <td class="p-3 text-sm text-[var(--color-text-muted)]">{{ p.outlet_name || '–' }}</td>
              <td class="p-3 text-sm">{{ formatDate(p.purchase_date || p.created_at) }}</td>
              <td class="p-3 text-sm">{{ (p.lines || []).length }}</td>
              <td class="p-3 text-sm text-[var(--color-text-muted)]">{{ p.created_by_name || '–' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Create Modal -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        <div class="p-5 flex-shrink-0">
          <h2 class="text-lg font-semibold text-[var(--color-text)]">New Purchase Order</h2>
        </div>
        <form @submit.prevent="submitPurchase" class="flex flex-col flex-1 min-h-0 overflow-hidden">
          <div class="p-5 space-y-4 overflow-y-auto flex-1">
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-[var(--color-text-muted)] mb-1">Outlet (ဆိုင်ခွဲ)</label>
                <p class="text-xs text-[var(--color-text-muted)] mb-1">ပစ္စည်းဝယ်ယူမည့် ဆိုင်ခွဲ ရွေးပါ</p>
                <select v-model="form.outlet" class="glass-input w-full px-3 py-2 rounded-lg" required>
                  <option value="">ရွေးပါ</option>
                  <option v-for="o in outlets" :key="o.id" :value="o.id">{{ o.name }}</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-[var(--color-text-muted)] mb-1">To Location</label>
                <select v-model="form.to_location" class="glass-input w-full px-3 py-2 rounded-lg" required>
                  <option value="">ရွေးပါ</option>
                  <option v-for="loc in locations" :key="loc.id" :value="loc.id">{{ loc.name }}</option>
                </select>
              </div>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-[var(--color-text-muted)] mb-1">Reference</label>
                <input v-model="form.reference" type="text" class="glass-input w-full px-3 py-2 rounded-lg" placeholder="PO-001" />
              </div>
              <div>
                <label class="block text-sm font-medium text-[var(--color-text-muted)] mb-1">Date</label>
                <input v-model="form.purchase_date" type="date" class="glass-input w-full px-3 py-2 rounded-lg" />
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-[var(--color-text-muted)] mb-1">Notes</label>
              <input v-model="form.notes" type="text" class="glass-input w-full px-3 py-2 rounded-lg" />
            </div>

            <div>
              <div class="flex items-center justify-between mb-2">
                <label class="text-sm font-medium text-[var(--color-text-muted)]">Lines</label>
                <button type="button" @click="addLine" class="text-sm font-medium text-[var(--color-primary)] hover:underline">+ Add line</button>
              </div>
              <div class="space-y-3">
                <div
                  v-for="(line, idx) in form.lines"
                  :key="idx"
                  class="flex flex-wrap items-end gap-2 p-3 rounded-lg bg-[var(--color-bg-light)]"
                >
                  <div class="flex-1 min-w-[140px]">
                    <label class="block text-xs text-[var(--color-text-muted)] mb-0.5">Product</label>
                    <select v-model="line.product" class="glass-input w-full px-2 py-1.5 rounded text-sm" required>
                      <option value="">ရွေးပါ</option>
                      <option v-for="prod in products" :key="prod.id" :value="prod.id">{{ prod.name }}</option>
                    </select>
                  </div>
                  <div class="w-24">
                    <label class="block text-xs text-[var(--color-text-muted)] mb-0.5">Unit</label>
                    <select v-model="line.purchase_unit" class="glass-input w-full px-2 py-1.5 rounded text-sm">
                      <option :value="null">–</option>
                      <option v-for="u in units" :key="u.id" :value="u.id">{{ u.name_en || u.code }}</option>
                    </select>
                  </div>
                  <div class="w-20">
                    <label class="block text-xs text-[var(--color-text-muted)] mb-0.5">Qty</label>
                    <input v-model.number="line.quantity" type="number" step="0.01" min="0.01" class="glass-input w-full px-2 py-1.5 rounded text-sm" required />
                  </div>
                  <div class="w-28">
                    <label class="block text-xs text-[var(--color-text-muted)] mb-0.5">Unit cost</label>
                    <input v-model.number="line.unit_cost" type="number" step="0.01" min="0" class="glass-input w-full px-2 py-1.5 rounded text-sm" />
                  </div>
                  <button type="button" @click="form.lines.splice(idx, 1)" class="p-1.5 rounded text-rose-600 hover:bg-rose-50">
                    <Trash2 class="w-4 h-4" />
                  </button>
                </div>
              </div>
              <p v-if="form.lines.length === 0" class="text-sm text-[var(--color-text-muted)]">အနည်းဆုံး ပစ္စည်းတစ်မျိုး ထည့်ပါ။</p>
            </div>
          </div>
          <div class="p-5 flex gap-3 flex-shrink-0 border-t border-[var(--color-border)]">
            <button type="button" @click="showModal = false" class="flex-1 btn-secondary py-2.5">Cancel</button>
            <button type="submit" :disabled="submitting || form.lines.length === 0" class="flex-1 btn-primary py-2.5">
              {{ submitting ? 'Saving...' : 'Save' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { Plus, Trash2 } from 'lucide-vue-next'
import api from '@/services/api'
import { useShopSettingsStore } from '@/stores/shopSettings'

const purchases = ref([])
const outlets = ref([])
const locations = ref([])
const products = ref([])
const units = ref([])
const loading = ref(false)
const showModal = ref(false)
const submitting = ref(false)

const form = ref({
  outlet: '',
  to_location: '',
  reference: '',
  purchase_date: new Date().toISOString().slice(0, 10),
  notes: '',
  lines: [{ product: '', purchase_unit: null, quantity: 1, unit_cost: 0 }],
})

function formatDate(val) {
  if (!val) return '–'
  return new Date(val).toISOString().slice(0, 10)
}

async function fetchPurchases() {
  loading.value = true
  try {
    const res = await api.get('purchases/')
    purchases.value = res.data?.results ?? res.data ?? []
  } catch {
    purchases.value = []
  } finally {
    loading.value = false
  }
}

async function fetchOutlets() {
  try {
    const res = await api.get('core/outlets/')
    outlets.value = res.data ?? []
  } catch {
    outlets.value = []
  }
}

async function fetchLocations() {
  try {
    const res = await api.get('locations/')
    const list = res.data?.results ?? res.data ?? []
    locations.value = Array.isArray(list) ? list : []
  } catch {
    locations.value = []
  }
}

async function fetchProducts() {
  try {
    const res = await api.get('staff/items/')
    const list = Array.isArray(res.data) ? res.data : (res.data?.results ?? [])
    products.value = list
  } catch {
    products.value = []
  }
}

async function fetchUnits() {
  try {
    const shopStore = useShopSettingsStore()
    const params = {}
    if (shopStore.filter_units_by_business_category && shopStore.business_category) params.business_category = shopStore.business_category
    const res = await api.get('units/', { params })
    units.value = res.data?.results ?? res.data ?? []
  } catch {
    units.value = []
  }
}

function addLine() {
  form.value.lines.push({ product: '', purchase_unit: null, quantity: 1, unit_cost: 0 })
}

function openCreate() {
  form.value = {
    outlet: outlets.value[0]?.id ?? '',
    to_location: locations.value[0]?.id ?? '',
    reference: '',
    purchase_date: new Date().toISOString().slice(0, 10),
    notes: '',
    lines: [{ product: '', purchase_unit: null, quantity: 1, unit_cost: 0 }],
  }
  showModal.value = true
}

async function submitPurchase() {
  if (form.value.lines.length === 0) {
    alert('အနည်းဆုံး ပစ္စည်းတစ်မျိုး ထည့်ပါ။')
    return
  }
  const invalid = form.value.lines.some((l) => !l.product || !l.quantity || l.quantity <= 0)
  if (invalid) {
    alert('ပစ္စည်းနဲ့ အရေအတွက် ဖြည့်ပါ။')
    return
  }

  submitting.value = true
  try {
    const payload = {
      outlet: form.value.outlet || null,
      to_location: form.value.to_location || null,
      reference: form.value.reference || '',
      purchase_date: form.value.purchase_date || null,
      notes: form.value.notes || '',
      lines: form.value.lines.map((l) => ({
        product: l.product,
        purchase_unit: l.purchase_unit || null,
        quantity: Number(l.quantity),
        unit_cost: Number(l.unit_cost) || 0,
      })),
    }
    await api.post('purchases/create/', payload)
    showModal.value = false
    await fetchPurchases()
    alert('သိမ်းဆည်းပြီးပါပြီ။')
  } catch (e) {
    const msg = e.response?.data ? (typeof e.response.data === 'string' ? e.response.data : JSON.stringify(e.response.data)) : e.message
    alert('သိမ်းဆည်း၍မရပါ။ ' + msg)
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  await Promise.all([fetchPurchases(), fetchOutlets(), fetchLocations(), fetchProducts(), fetchUnits()])
  if (form.value.outlet === '' && outlets.value.length) form.value.outlet = outlets.value[0].id
  if (form.value.to_location === '' && locations.value.length) form.value.to_location = locations.value[0].id
})
</script>
