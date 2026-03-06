<template>
  <div class="space-y-6 text-[#1a1a1a]">
    <div v-if="!hideHeader" class="flex flex-wrap justify-between items-center gap-4">
      <h1 class="text-xl font-semibold text-[#1a1a1a]">အတွဲ စီမံခန့်ခွဲမှု (Set / Bundle)</h1>
      <button
        @click="openAddModal"
        class="loyverse-btn-primary px-5 py-2.5 flex items-center gap-2 rounded-xl text-sm font-medium text-white"
      >
        <Plus class="w-4 h-4" /> အတွဲအသစ်ထည့်မည်
      </button>
    </div>

    <FilterDataTable
      ref="tableRef"
      title="အတွဲများ"
      :light="hideHeader"
      :columns="columns"
      :data="bundles"
      :total-count="totalCount"
      :loading="loading"
      search-placeholder="အတွဲအမည် / SKU ရှာပါ..."
      :default-page-size="20"
      empty-message="အတွဲ မရှိသေးပါ။"
      @fetch-data="fetchData"
    >
      <template #cell-name="{ value }">
        <span class="font-semibold text-[#1a1a1a]">{{ value }}</span>
      </template>
      <template #cell-bundle_type="{ value }">
        <span class="text-sm">{{ value || '–' }}</span>
      </template>
      <template #cell-total_price="{ value }">
        <span class="text-sm">{{ value != null ? `${Number(value).toLocaleString()} MMK` : '–' }}</span>
      </template>
      <template #cell-is_active="{ value }">
        <span :class="value ? 'text-emerald-600' : 'text-[var(--color-fg-muted)]'">{{ value ? 'ဖွင့်' : 'ပိတ်' }}</span>
      </template>
      <template #actions="{ row }">
        <div class="flex items-center justify-end gap-2">
          <button @click="openEditModal(row)" class="text-[var(--loyverse-blue)] font-medium text-sm hover:underline">ပြင်မည်</button>
          <button @click="deleteBundle(row.id)" class="text-rose-600 font-medium text-sm hover:underline">ဖျက်မည်</button>
        </div>
      </template>
    </FilterDataTable>

    <!-- Add/Edit Modal -->
    <div v-if="showModal" class="fixed inset-0 z-[100] flex items-center justify-center p-4 overflow-y-auto">
      <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="showModal = false" />
      <div class="bg-white w-full max-w-2xl my-8 p-8 relative z-10 rounded-xl border border-[var(--color-border)] shadow-xl">
        <h3 class="text-xl font-semibold text-[#1a1a1a] mb-6">
          {{ isEdit ? 'အတွဲ ပြင်ဆင်မည်' : 'အတွဲ အသစ်ထည့်မည်' }}
        </h3>
        <form @submit.prevent="saveBundle" class="space-y-5">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block mb-2 text-sm font-medium text-[#374151]">အတွဲအမည်</label>
              <input v-model="form.name" type="text" required class="glass-input w-full px-4 py-3 rounded-xl" placeholder="ဥပမာ - ဖုန်းတစ်စုံပါအတွဲ" />
            </div>
            <div>
              <label class="block mb-2 text-sm font-medium text-[#374151]">SKU / ကုဒ်</label>
              <input v-model="form.sku" type="text" class="glass-input w-full px-4 py-3 rounded-xl" placeholder="Optional" />
            </div>
          </div>
          <div>
            <label class="block mb-2 text-sm font-medium text-[#374151]">ဖော်ပြချက်</label>
            <textarea v-model="form.description" class="glass-input w-full px-4 py-3 rounded-xl" rows="2" placeholder="Optional" />
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block mb-2 text-sm font-medium text-[#374151]">အတွဲအမျိုးအစား</label>
              <select v-model="form.bundle_type" class="glass-input w-full px-4 py-3 rounded-xl">
                <option value="Fixed">Fixed (အစုလိုက်)</option>
                <option value="PC">PC Building</option>
                <option value="Solar">Solar Set</option>
                <option value="Machine">Machinery Package</option>
              </select>
            </div>
            <div>
              <label class="block mb-2 text-sm font-medium text-[#374151]">ဈေးနှုန်း (သတ်မှတ်ပါက)</label>
              <input v-model.number="form.bundle_price" type="number" min="0" step="0.01" class="glass-input w-full px-4 py-3 rounded-xl" placeholder="ဗလာထားရင် ပစ္စည်းဈေးပေါင်း" />
            </div>
          </div>
          <div class="flex items-center gap-4">
            <label class="flex items-center gap-2 cursor-pointer">
              <input v-model="form.is_active" type="checkbox" class="w-4 h-4 rounded border-border" />
              <span class="text-sm font-medium">အသက်သွင်းထား</span>
            </label>
          </div>

          <div>
            <div class="flex justify-between items-center mb-2">
              <label class="text-sm font-medium text-[#374151]">ပါဝင်ပစ္စည်းများ</label>
              <button type="button" @click="addItemRow" class="text-sm text-[var(--loyverse-blue)] hover:underline">+ ပစ္စည်းထပ်ထည့်မည်</button>
            </div>
            <div v-for="(item, idx) in form.items" :key="idx" class="flex flex-wrap items-center gap-2 mb-2 p-2 bg-[var(--color-bg-subtle)] rounded-lg">
              <select v-model="item.product" required class="glass-input flex-1 min-w-[120px] px-3 py-2 rounded-lg text-sm">
                <option :value="null">ပစ္စည်းရွေးပါ</option>
                <option v-for="p in products" :key="p.id" :value="p.id">{{ p.name }} ({{ p.sku || p.id }})</option>
              </select>
              <input v-model.number="item.quantity" type="number" min="1" class="glass-input w-20 px-3 py-2 rounded-lg text-sm" />
              <label class="flex items-center gap-1 text-sm whitespace-nowrap">
                <input v-model="item.is_optional" type="checkbox" class="w-4 h-4 rounded" />
                ရွေးချယ်မှု
              </label>
              <button type="button" @click="form.items.splice(idx, 1)" class="text-rose-600 p-1" title="ဖယ်မည်">×</button>
            </div>
            <p v-if="form.items.length === 0" class="text-sm text-[var(--color-fg-muted)]">ပစ္စည်း အနည်းဆုံး တစ်ခု ထည့်ပါ။</p>
          </div>

          <div class="flex gap-3 pt-4">
            <button type="button" @click="showModal = false" class="loyverse-btn-secondary flex-1 py-3 rounded-xl">ပယ်မည်</button>
            <button type="submit" :disabled="submitting || form.items.length === 0" class="loyverse-btn-primary flex-1 py-3 rounded-xl text-white disabled:opacity-50">
              {{ submitting ? 'သိမ်းနေသည်...' : 'သိမ်းမည်' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { getLoginPath } from '@/router'
import { Plus } from 'lucide-vue-next'
import FilterDataTable from '@/components/FilterDataTable.vue'
import api from '@/services/api'

defineProps({
  hideHeader: { type: Boolean, default: false },
})
defineExpose({ openAddModal })

const router = useRouter()
const tableRef = ref(null)
const bundles = ref([])
const totalCount = ref(0)
const loading = ref(false)
const showModal = ref(false)
const submitting = ref(false)
const isEdit = ref(false)
const currentId = ref(null)
const products = ref([])

const defaultForm = () => ({
  name: '',
  description: '',
  sku: '',
  bundle_type: 'Fixed',
  bundle_price: null,
  pricing_type: 'CUSTOM_SET',
  is_active: true,
  items: [{ product: null, quantity: 1, is_optional: false }],
})

const form = ref(defaultForm())

const columns = [
  { key: 'name', label: 'အတွဲအမည်', sortable: true },
  { key: 'sku', label: 'SKU', sortable: true },
  { key: 'bundle_type', label: 'အမျိုးအစား', sortable: true },
  { key: 'items_count', label: 'ပစ္စည်းအရေအတွက်', sortable: false },
  { key: 'total_price', label: 'ဈေးနှုန်း', sortable: false },
  { key: 'is_active', label: 'အခြေအနေ', sortable: true },
]

function fetchData({ search, page, pageSize, ordering }) {
  loading.value = true
  const params = { page, page_size: pageSize }
  if (search) params.search = search
  if (ordering) params.ordering = ordering
  api
    .get('bundles/', { params })
    .then((res) => {
      bundles.value = res.data.results ?? res.data ?? []
      totalCount.value = res.data.count ?? bundles.value.length
    })
    .catch((err) => {
      if (err.response?.status === 401) router.push(getLoginPath())
      else bundles.value = []
      totalCount.value = 0
    })
    .finally(() => (loading.value = false))
}

async function loadProducts() {
  try {
    const res = await api.get('products-admin/', { params: { page_size: 500 } })
    products.value = res.data.results ?? res.data ?? []
  } catch {
    products.value = []
  }
}

function addItemRow() {
  form.value.items.push({ product: null, quantity: 1, is_optional: false })
}

async function saveBundle() {
  const payload = {
    name: form.value.name,
    description: form.value.description || null,
    sku: form.value.sku || null,
    bundle_type: form.value.bundle_type,
    bundle_price: form.value.bundle_price || null,
    pricing_type: form.value.pricing_type,
    is_active: form.value.is_active,
    items: form.value.items.filter((i) => i.product != null).map((i, idx) => ({
      product: i.product,
      quantity: i.quantity,
      is_optional: !!i.is_optional,
      sort_order: idx,
    })),
  }
  if (payload.items.length === 0) {
    alert('ပစ္စည်း အနည်းဆုံး တစ်ခု ရွေးပါ။')
    return
  }
  submitting.value = true
  try {
    if (isEdit.value) {
      await api.patch(`bundles/${currentId.value}/`, payload)
    } else {
      await api.post('bundles/', payload)
    }
    showModal.value = false
    tableRef.value?.emitFetch()
  } catch (err) {
    if (err.response?.status === 401) router.push(getLoginPath())
    else alert(err.response?.data?.detail || err.response?.data?.items?.[0] || 'သိမ်းမရပါ။')
  } finally {
    submitting.value = false
  }
}

function openAddModal() {
  isEdit.value = false
  form.value = defaultForm()
  loadProducts()
  showModal.value = true
}

async function openEditModal(bundle) {
  isEdit.value = true
  currentId.value = bundle.id
  loadProducts()
  try {
    const res = await api.get(`bundles/${bundle.id}/`)
    const d = res.data
    form.value = {
      name: d.name,
      description: d.description || '',
      sku: d.sku || '',
      bundle_type: d.bundle_type || 'Fixed',
      bundle_price: d.bundle_price != null ? Number(d.bundle_price) : null,
      pricing_type: d.pricing_type || 'CUSTOM_SET',
      is_active: d.is_active !== false,
      items: (d.items || []).length ? d.items.map((i) => ({ product: i.product, quantity: i.quantity, is_optional: !!i.is_optional })) : [{ product: null, quantity: 1, is_optional: false }],
    }
  } catch (err) {
    if (err.response?.status === 401) router.push(getLoginPath())
    else form.value = defaultForm()
  }
  showModal.value = true
}

async function deleteBundle(id) {
  if (!confirm('ဤအတွဲကို ဖျက်မည်ဟု သေချာပါသလား?')) return
  try {
    await api.delete(`bundles/${id}/`)
    tableRef.value?.emitFetch()
  } catch (err) {
    alert('ဖျက်မရပါ။')
  }
}

</script>
