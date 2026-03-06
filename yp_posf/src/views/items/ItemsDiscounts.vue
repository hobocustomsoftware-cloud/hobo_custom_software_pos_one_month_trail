<template>
  <div class="bg-white border border-[var(--color-border)] rounded-xl p-6">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-lg font-bold text-[var(--color-text)] flex items-center gap-2">
        <Percent class="w-5 h-5 text-[var(--color-primary)]" />
        လျှော့ဈေး စည်းမျဉ်းများ
      </h2>
      <button
        @click="openAddModal"
        class="px-4 py-2 rounded-xl bg-[var(--color-primary)] text-white font-bold text-sm hover:opacity-90 transition-all flex items-center gap-2"
      >
        <Plus class="w-4 h-4" />
        ထည့်ရန်
      </button>
    </div>

    <div v-if="loading" class="text-center py-8 text-[var(--color-text-muted)] text-base">Loading...</div>

    <div v-else class="space-y-3">
      <div
        v-for="rule in rules"
        :key="rule.id"
        class="p-4 bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl hover:bg-[var(--color-bg-light)] transition-all"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="flex items-center gap-3 mb-2">
              <h3 class="font-bold text-[var(--color-text)]">{{ rule.name }}</h3>
              <span
                :class="rule.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-gray-100 text-gray-600'"
                class="px-2 py-1 rounded text-xs font-bold"
              >
                {{ rule.is_active ? 'အသက်သွင်း' : 'ပိတ်ထား' }}
              </span>
            </div>
            <p class="text-sm text-[var(--color-text-muted)]">
              {{ rule.discount_type === 'PERCENTAGE' ? rule.value + '%' : rule.value + ' MMK' }}
              <span v-if="rule.min_purchase" class="ml-2">(အနည်းဆုံး {{ rule.min_purchase }} MMK)</span>
            </p>
            <p v-if="rule.start_date || rule.end_date" class="text-xs text-[var(--color-text-subtle)] mt-1">
              {{ rule.start_date || '–' }} ~ {{ rule.end_date || '–' }}
            </p>
          </div>
          <div class="flex items-center gap-2 ml-4">
            <button
              @click="editRule(rule)"
              class="p-2 rounded-lg text-[var(--color-primary)] hover:bg-[var(--color-bg-light)] transition"
            >
              <Edit class="w-4 h-4" />
            </button>
            <button
              @click="deleteRule(rule.id)"
              class="p-2 rounded-lg text-rose-600 hover:bg-rose-50 transition"
            >
              <Trash2 class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      <div v-if="rules.length === 0" class="text-center py-8 text-[var(--color-text-muted)] text-base">
        လျှော့ဈေး စည်းမျဉ်း မရှိပါ။ ထည့်ရန် နှိပ်ပါ။
      </div>
    </div>

    <!-- Add/Edit Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white border border-[var(--color-border)] rounded-xl max-w-md w-full p-6 space-y-4 shadow-lg">
        <h3 class="text-xl font-bold text-[var(--color-text)]">
          {{ editingRule ? 'ပြင်ဆင်ရန်' : 'အသစ်ထည့်ရန်' }}
        </h3>

        <div>
          <label class="block mb-2 text-sm font-medium text-[var(--color-text-muted)]">အမည်</label>
          <input
            v-model="form.name"
            type="text"
            class="glass-input w-full px-4 py-2 rounded-xl"
            placeholder="ဥပမာ: ၁၀% လျှော့ဈေး"
            required
          />
        </div>

        <div>
          <label class="block mb-2 text-sm font-medium text-[var(--color-text-muted)]">အမျိုးအစား</label>
          <select v-model="form.discount_type" class="glass-input w-full px-4 py-2 rounded-xl">
            <option value="PERCENTAGE">ရာခိုင်နှုန်း (%)</option>
            <option value="FIXED_AMOUNT">သတ်မှတ်ပမာဏ (MMK)</option>
          </select>
        </div>

        <div>
          <label class="block mb-2 text-sm font-medium text-[var(--color-text-muted)]">
            {{ form.discount_type === 'PERCENTAGE' ? 'ရာခိုင်နှုန်း' : 'ပမာဏ (MMK)' }}
          </label>
          <input
            v-model.number="form.value"
            type="number"
            step="0.01"
            min="0"
            class="glass-input w-full px-4 py-2 rounded-xl"
            placeholder="0"
          />
        </div>

        <div>
          <label class="block mb-2 text-sm font-medium text-[var(--color-text-muted)]">အနည်းဆုံး ဝယ်ယူငွေ (MMK) – ရွေးချယ်နိုင်</label>
          <input
            v-model.number="form.min_purchase"
            type="number"
            step="0.01"
            min="0"
            class="glass-input w-full px-4 py-2 rounded-xl"
            placeholder=""
          />
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block mb-2 text-sm font-medium text-[var(--color-text-muted)]">စတင်ရက်</label>
            <input v-model="form.start_date" type="date" class="glass-input w-full px-4 py-2 rounded-xl" />
          </div>
          <div>
            <label class="block mb-2 text-sm font-medium text-[var(--color-text-muted)]">ပြီးဆုံးရက်</label>
            <input v-model="form.end_date" type="date" class="glass-input w-full px-4 py-2 rounded-xl" />
          </div>
        </div>

        <div class="flex items-center gap-2">
          <input
            id="form-active"
            v-model="form.is_active"
            type="checkbox"
            class="rounded border-[var(--color-border)]"
          />
          <label for="form-active" class="text-sm font-medium text-[var(--color-text)]">အသက်သွင်းထား</label>
        </div>

        <div class="flex gap-3 pt-4">
          <button
            @click="saveRule"
            :disabled="saving"
            class="flex-1 px-4 py-2 rounded-xl bg-[var(--color-primary)] text-white font-bold hover:opacity-90 transition-all disabled:opacity-70"
          >
            {{ saving ? 'သိမ်းနေသည်...' : 'သိမ်းဆည်းရန်' }}
          </button>
          <button
            @click="closeModal"
            class="flex-1 px-4 py-2 rounded-xl border border-[var(--color-border)] bg-white text-[var(--color-text)] font-bold hover:bg-[var(--color-bg-light)] transition-all"
          >
            ပယ်ဖျက်ရန်
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Percent, Plus, Edit, Trash2 } from 'lucide-vue-next'
import api from '@/services/api'

const rules = ref([])
const loading = ref(false)
const saving = ref(false)
const showModal = ref(false)
const editingRule = ref(null)

const form = ref({
  name: '',
  discount_type: 'PERCENTAGE',
  value: 0,
  min_purchase: null,
  start_date: '',
  end_date: '',
  is_active: true,
})

const fetchRules = async () => {
  loading.value = true
  try {
    const res = await api.get('discount-rules/')
    rules.value = res.data.results ?? res.data ?? []
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const openAddModal = () => {
  editingRule.value = null
  form.value = {
    name: '',
    discount_type: 'PERCENTAGE',
    value: 0,
    min_purchase: null,
    start_date: '',
    end_date: '',
    is_active: true,
  }
  showModal.value = true
}

const editRule = (rule) => {
  editingRule.value = rule
  form.value = {
    name: rule.name,
    discount_type: rule.discount_type,
    value: rule.value,
    min_purchase: rule.min_purchase ?? null,
    start_date: rule.start_date || '',
    end_date: rule.end_date || '',
    is_active: rule.is_active,
  }
  showModal.value = true
}

const saveRule = async () => {
  if (!form.value.name.trim()) {
    alert('ကျေးဇူးပြု၍ အမည် ဖြည့်သွင်းပါ။')
    return
  }

  saving.value = true
  try {
    const payload = {
      ...form.value,
      min_purchase: form.value.min_purchase || null,
      start_date: form.value.start_date || null,
      end_date: form.value.end_date || null,
    }
    if (editingRule.value) {
      await api.patch(`discount-rules/${editingRule.value.id}/`, payload)
    } else {
      await api.post('discount-rules/', payload)
    }
    await fetchRules()
    closeModal()
    alert('သိမ်းဆည်းပြီးပါပြီ။')
  } catch (error) {
    console.error(error)
    alert('သိမ်းဆည်းခြင်း မအောင်မြင်ပါ။ ' + (error.response?.data?.detail || error.response?.data?.error || error.message))
  } finally {
    saving.value = false
  }
}

const deleteRule = async (id) => {
  if (!confirm('ဤ လျှော့ဈေး စည်းမျဉ်းကို ဖျက်ရန် သေချာပါသလား?')) return
  try {
    await api.delete(`discount-rules/${id}/`)
    await fetchRules()
    alert('ဖျက်ပြီးပါပြီ။')
  } catch (error) {
    console.error(error)
    alert('ဖျက်ခြင်း မအောင်မြင်ပါ။ ' + (error.response?.data?.detail || error.message))
  }
}

const closeModal = () => {
  showModal.value = false
  editingRule.value = null
}

onMounted(() => {
  fetchRules()
})
</script>
