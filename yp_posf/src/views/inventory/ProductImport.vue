<template>
  <div class="product-import space-y-6 max-w-4xl mx-auto p-4 md:p-6 text-[var(--color-fg)]">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-[var(--color-fg)]">ပစ္စည်း Excel/CSV ထည့်သွင်းခြင်း</h1>
        <p class="text-sm text-[var(--color-fg-muted)] mt-1">Excel (.xlsx, .xls) သို့မဟုတ် CSV ဖိုင်ရွေးပြီး ကော်လံ ချိတ်ဆက်ပါ။</p>
      </div>
      <router-link
        :to="{ name: 'Products' }"
        class="px-4 py-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] text-sm font-medium hover:bg-[var(--color-bg-light)]"
      >
        ← ပစ္စည်းစာရင်း
      </router-link>
    </div>

    <div class="bg-white rounded-xl border border-[var(--color-border)] shadow-sm p-6 space-y-6">
      <!-- Step 1: File -->
      <div>
        <label class="block text-sm font-medium text-[var(--color-fg)] mb-2">၁။ ဖိုင်ရွေးပါ (Excel / CSV)</label>
        <input
          ref="fileInputRef"
          type="file"
          accept=".xlsx,.xls,.csv"
          class="block w-full text-sm text-[var(--color-fg-muted)] file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border file:border-[var(--color-border)] file:bg-[var(--color-bg-light)] file:font-medium file:text-[var(--color-fg)] hover:file:bg-[var(--color-bg-card)]"
          @change="onFileSelect"
        />
        <p v-if="fileName" class="mt-2 text-sm text-[var(--color-fg-muted)]">ရွေးထားသော ဖိုင်: {{ fileName }}</p>
      </div>

      <!-- Step 2: Mapping (after preview) -->
      <div v-if="columns.length > 0" class="space-y-4">
        <h2 class="text-base font-semibold text-[var(--color-fg)]">၂။ ကော်လံ ချိတ်ဆက်မှု</h2>
        <p class="text-sm text-[var(--color-fg-muted)]">ဖိုင်ထဲက ကော်လံတစ်ခုချင်းကို စနစ်ထဲက အကွက်နဲ့ ရွေးချယ်ပါ။</p>
        <div class="overflow-x-auto">
          <table class="w-full border border-[var(--color-border)] rounded-lg overflow-hidden">
            <thead class="bg-[var(--color-bg-card)]">
              <tr>
                <th class="p-3 text-left text-xs font-semibold text-[var(--color-fg-muted)]">ဖိုင်က ကော်လံ</th>
                <th class="p-3 text-left text-xs font-semibold text-[var(--color-fg-muted)]">ပြီးပြည့်စုံမှု (ပထမတန်း)</th>
                <th class="p-3 text-left text-xs font-semibold text-[var(--color-fg-muted)]">စနစ်ထဲက အကွက်</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(col, i) in columns" :key="i" class="border-t border-[var(--color-border)]">
                <td class="p-3 font-medium text-[var(--color-fg)]">{{ col }}</td>
                <td class="p-3 text-sm text-[var(--color-fg-muted)] truncate max-w-[200px]">{{ sample[i] }}</td>
                <td class="p-3">
                  <select
                    v-model="mapping[col]"
                    class="w-full max-w-[220px] px-3 py-2 rounded-lg border border-[var(--color-border)] bg-white text-sm text-[var(--color-fg)]"
                  >
                    <option value="">— မချိတ်ပါ —</option>
                    <option value="name">ပစ္စည်းအမည် (name) *</option>
                    <option value="sku">SKU / Barcode</option>
                    <option value="model_no">Model No.</option>
                    <option value="category_name">Category အမည်</option>
                    <option value="retail_price">အရောင်းဈေး (retail_price)</option>
                    <option value="cost_price">ကုန်ကျဈေး (cost_price)</option>
                    <option value="quantity">ပမာဏ (stock)</option>
                    <option value="warranty_months">Warranty (လ)</option>
                    <option value="is_serial_tracked">Serial ခြေရာခံ</option>
                    <option value="serial_number_required">Serial လိုအပ်သည်</option>
                  </select>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Location (optional) -->
      <div v-if="columns.length > 0" class="flex flex-wrap items-center gap-4">
        <label class="text-sm font-medium text-[var(--color-fg)]">Stock ထည့်မည့်နေရာ (optional)</label>
        <select
          v-model="locationId"
          class="px-4 py-2 rounded-lg border border-[var(--color-border)] bg-white text-sm text-[var(--color-fg)]"
        >
          <option value="">— မရွေးပါ —</option>
          <option v-for="loc in locations" :key="loc.id" :value="loc.id">{{ loc.name }}</option>
        </select>
      </div>

      <!-- Actions -->
      <div class="flex flex-wrap gap-3 pt-2">
        <button
          type="button"
          :disabled="!selectedFile || loading"
          class="px-5 py-2.5 rounded-xl font-medium text-white bg-[var(--loyverse-blue)] hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
          @click="doImport"
        >
          {{ loading ? 'ထည့်သွင်းနေပါသည်...' : 'ထည့်သွင်းမည် (Import)' }}
        </button>
        <button
          type="button"
          class="px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] font-medium text-[var(--color-fg)] hover:bg-[var(--color-bg-light)]"
          @click="reset"
        >
          ပြန်စမည်
        </button>
      </div>

      <!-- Result -->
      <div v-if="result" class="p-4 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] space-y-2">
        <h3 class="font-semibold text-[var(--color-fg)]">ရလဒ်</h3>
        <p class="text-sm text-[var(--color-fg)]">အသစ်ထည့်သွင်း: <strong>{{ result.imported }}</strong> | ပြင်ဆင်ပြီး stock: <strong>{{ result.updated }}</strong> | မအောင်မြင်: <strong>{{ result.failed }}</strong></p>
        <div v-if="result.errors && result.errors.length > 0" class="mt-2">
          <p class="text-xs font-medium text-rose-600 mb-1">အမှားများ (ပထမ ၁၀ ခု):</p>
          <ul class="text-xs text-[var(--color-fg-muted)] list-disc list-inside space-y-0.5">
            <li v-for="(err, i) in result.errors.slice(0, 10)" :key="i">Row {{ err.row }}: {{ err.reason }}</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import { useToast } from '@/composables/useToast'

const toast = useToast()
const fileInputRef = ref(null)
const selectedFile = ref(null)
const fileName = ref('')
const columns = ref([])
const sample = ref([])
const mapping = ref({})
const locationId = ref('')
const locations = ref([])
const loading = ref(false)
const result = ref(null)

async function fetchLocations() {
  try {
    const res = await api.get('locations/')
    locations.value = res.data?.results ?? res.data ?? []
  } catch {
    locations.value = []
  }
}

function onFileSelect(ev) {
  const file = ev.target?.files?.[0]
  if (!file) return
  const n = (file.name || '').toLowerCase()
  if (!n.endsWith('.xlsx') && !n.endsWith('.xls') && !n.endsWith('.csv')) {
    toast.error('Excel (.xlsx, .xls) သို့မဟုတ် CSV ဖိုင်သာ ရွေးပါ။')
    return
  }
  selectedFile.value = file
  fileName.value = file.name
  result.value = null
  loadPreview()
}

async function loadPreview() {
  if (!selectedFile.value) return
  loading.value = true
  columns.value = []
  sample.value = []
  mapping.value = {}
  try {
    const form = new FormData()
    form.append('file', selectedFile.value)
    const res = await api.post('products/import/preview/', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    columns.value = res.data.columns || []
    sample.value = res.data.sample || []
    columns.value.forEach((c) => { mapping.value[c] = '' })
  } catch (e) {
    toast.error(e.response?.data?.error || 'ဖိုင်ဖတ်၍မရပါ။')
  } finally {
    loading.value = false
  }
}

async function doImport() {
  if (!selectedFile.value) return
  const mapFiltered = Object.fromEntries(Object.entries(mapping.value).filter(([, v]) => v))
  if (!mapFiltered.name) {
    toast.error('ပစ္စည်းအမည် (name) ချိတ်ဆက်ရန် လိုအပ်ပါသည်။')
    return
  }
  loading.value = true
  result.value = null
  try {
    const form = new FormData()
    form.append('file', selectedFile.value)
    form.append('mapping', JSON.stringify(mapFiltered))
    if (locationId.value) form.append('location_id', locationId.value)
    const res = await api.post('products/import/', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    result.value = res.data
    toast.success(`ထည့်သွင်းပြီး: ${res.data.imported} | ပြင်ဆင်: ${res.data.updated} | မအောင်: ${res.data.failed}`)
  } catch (e) {
    toast.error(e.response?.data?.error || 'ထည့်သွင်းမှု မအောင်မြင်ပါ။')
  } finally {
    loading.value = false
  }
}

function reset() {
  selectedFile.value = null
  fileName.value = ''
  columns.value = []
  sample.value = []
  mapping.value = {}
  result.value = null
  if (fileInputRef.value) fileInputRef.value.value = ''
}

onMounted(() => {
  fetchLocations()
})
</script>
