<template>
  <div class="w-full max-w-6xl mx-auto px-2 sm:px-4 space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div>
        <h1 class="text-lg sm:text-xl font-semibold text-[var(--color-fg)]">Stock Counts</h1>
        <p class="text-sm text-[var(--color-fg-muted)]">Stock count and variance.</p>
      </div>
      <button type="button" @click="openNewCount" class="btn-primary px-4 py-2 flex items-center gap-2">
        <Plus class="w-4 h-4" /> New count
      </button>
    </div>

    <div class="bg-white rounded-xl shadow-sm overflow-hidden min-h-[200px]">
      <div v-if="loading" class="p-8 text-center text-[var(--color-fg-muted)]">Loading...</div>
      <div v-else-if="products.length === 0" class="p-8 text-center text-[var(--color-fg-muted)]">
        ပစ္စည်းစာရင်း မရှိသေးပါ။
      </div>
      <div v-else class="overflow-x-auto">
        <table class="w-full min-w-[400px]">
          <thead class="bg-[var(--color-bg-light)]">
            <tr>
              <th class="p-3 text-left text-sm font-semibold text-[var(--color-fg)]">Product</th>
              <th class="p-3 text-left text-sm font-semibold text-[var(--color-fg)]">SKU</th>
              <th class="p-3 text-right text-sm font-semibold text-[var(--color-fg)]">Current stock</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[var(--color-border)]">
            <tr v-for="p in products" :key="p.id" class="hover:bg-[var(--color-bg-light)]">
              <td class="p-3 font-medium">{{ p.name }}</td>
              <td class="p-3 text-sm text-[var(--color-fg-muted)]">{{ p.sku || '–' }}</td>
              <td class="p-3 text-right font-medium">{{ formatQty(p.current_stock ?? p.total_stock) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- New count modal -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" @click.self="showModal = false">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-hidden flex flex-col" @click.stop>
        <div class="p-4 border-b border-[var(--color-border)]">
          <h2 class="text-lg font-semibold">New stock count</h2>
          <p class="text-xs text-[var(--color-fg-muted)] mt-1">တည်နေရာရွေးပြီး ပစ္စည်းအလိုက် ရေတွက်ပမာဏ ထည့်ပါ။</p>
        </div>
        <form @submit.prevent="submitCount" class="flex flex-col flex-1 min-h-0 overflow-hidden">
          <div class="p-4 overflow-y-auto flex-1 space-y-4">
            <div>
              <label class="block text-sm font-medium text-[var(--color-fg-muted)] mb-1">Location</label>
              <select v-model="countForm.location" class="glass-input w-full px-3 py-2 rounded-lg" required>
                <option value="">ရွေးပါ</option>
                <option v-for="loc in locations" :key="loc.id" :value="loc.id">{{ loc.name }}</option>
              </select>
            </div>
            <div>
              <div class="flex items-center justify-between mb-2">
                <label class="text-sm font-medium text-[var(--color-fg-muted)]">Lines</label>
                <button type="button" @click="addCountLine" class="text-sm text-[var(--color-primary)] hover:underline">+ Add line</button>
              </div>
              <div class="space-y-2">
                <div
                  v-for="(line, idx) in countForm.lines"
                  :key="idx"
                  class="flex flex-wrap items-center gap-2 p-2 rounded-lg bg-[var(--color-bg-light)]"
                >
                  <select v-model="line.product" class="flex-1 min-w-[120px] glass-input px-2 py-1.5 rounded text-sm" required>
                    <option value="">Product</option>
                    <option v-for="p in products" :key="p.id" :value="p.id">{{ p.name }}</option>
                  </select>
                  <input v-model.number="line.counted_quantity" type="number" step="0.01" min="0" placeholder="Counted" class="w-24 glass-input px-2 py-1.5 rounded text-sm" required />
                  <button type="button" @click="countForm.lines.splice(idx, 1)" class="p-1 text-rose-600 hover:bg-rose-50 rounded">
                    <Trash2 class="w-4 h-4" />
                  </button>
                </div>
              </div>
              <p v-if="countForm.lines.length === 0" class="text-sm text-[var(--color-fg-muted)] mt-1">အနည်းဆုံး တစ်မျိုး ထည့်ပါ။</p>
            </div>
          </div>
          <div class="p-4 border-t border-[var(--color-border)] flex gap-2">
            <button type="button" @click="showModal = false" class="flex-1 btn-secondary py-2">Cancel</button>
            <button type="submit" :disabled="submitting || countForm.lines.length === 0" class="flex-1 btn-primary py-2">
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
import { Plus, Trash2 } from 'lucide-vue-next'
import api from '@/services/api'

const products = ref([])
const locations = ref([])
const loading = ref(false)
const showModal = ref(false)
const submitting = ref(false)

const countForm = ref({
  location: '',
  lines: [{ product: '', counted_quantity: 0 }],
})

function formatQty(v) {
  if (v == null) return '–'
  const n = Number(v)
  return Number.isFinite(n) ? n.toLocaleString(undefined, { maximumFractionDigits: 2 }) : v
}

async function fetchProducts() {
  loading.value = true
  try {
    const res = await api.get('staff/items/')
    products.value = Array.isArray(res.data) ? res.data : (res.data?.results ?? [])
  } catch {
    products.value = []
  } finally {
    loading.value = false
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

function addCountLine() {
  countForm.value.lines.push({ product: '', counted_quantity: 0 })
}

function openNewCount() {
  countForm.value = {
    location: locations.value[0]?.id ?? '',
    lines: [{ product: '', counted_quantity: 0 }],
  }
  showModal.value = true
}

async function submitCount() {
  const valid = countForm.value.lines.filter((l) => l.product && (l.counted_quantity !== '' && l.counted_quantity != null))
  if (!countForm.value.location || valid.length === 0) {
    alert('Location နဲ့ အနည်းဆုံး ပစ္စည်းတစ်မျိုး ထည့်ပါ။')
    return
  }
  submitting.value = true
  try {
    await api.post('stock-count/', {
      location: countForm.value.location,
      lines: valid.map((l) => ({
        product: l.product,
        counted_quantity: Number(l.counted_quantity) || 0,
      })),
    })
    showModal.value = false
    await fetchProducts()
    alert('သိမ်းပြီးပါပြီ။')
  } catch (e) {
    const msg = e.response?.data?.error || e.message || 'သိမ်း၍မရပါ။'
    alert(msg)
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  await Promise.all([fetchProducts(), fetchLocations()])
  if (countForm.value.location === '' && locations.value.length) countForm.value.location = locations.value[0].id
})
</script>
