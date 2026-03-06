<template>
  <div class="bg-white border border-[var(--color-border)] rounded-xl p-6">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-lg font-bold text-[var(--color-text)] flex items-center gap-2">
        <Layers class="w-5 h-5 text-[var(--color-primary)]" />
        Modifier အုပ်စုများ (အရွယ်အစား / အပိုများ)
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
        v-for="group in groups"
        :key="group.id"
        class="p-4 bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl hover:bg-[var(--color-bg-light)] transition-all"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="flex items-center gap-3 mb-2">
              <h3 class="font-bold text-[var(--color-text)]">{{ group.name }}</h3>
              <span
                :class="group.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-gray-100 text-gray-600'"
                class="px-2 py-1 rounded text-xs font-bold"
              >
                {{ group.is_active ? 'အသက်သွင်း' : 'ပိတ်ထား' }}
              </span>
              <span v-if="group.is_required" class="text-xs text-[var(--color-text-muted)]">ရွေးရမည်</span>
            </div>
            <p v-if="group.description" class="text-sm text-[var(--color-text-muted)] mb-2">{{ group.description }}</p>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="opt in (group.options || [])"
                :key="opt.id"
                class="px-2 py-1 rounded-lg text-xs bg-[var(--color-bg-light)] border border-[var(--color-border)] text-[var(--color-text)]"
              >
                {{ opt.name }} {{ opt.price_adjustment ? `+${opt.price_adjustment} MMK` : '' }}
              </span>
            </div>
          </div>
          <div class="flex items-center gap-2 ml-4">
            <button
              @click="editGroup(group)"
              class="p-2 rounded-lg text-[var(--color-primary)] hover:bg-[var(--color-bg-light)] transition"
            >
              <Edit class="w-4 h-4" />
            </button>
            <button
              @click="deleteGroup(group.id)"
              class="p-2 rounded-lg text-rose-600 hover:bg-rose-50 transition"
            >
              <Trash2 class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      <div v-if="groups.length === 0" class="text-center py-8 text-[var(--color-text-muted)] text-base">
        Modifier အုပ်စု မရှိပါ။ ထည့်ရန် နှိပ်ပါ။
      </div>
    </div>

    <!-- Add/Edit Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div class="bg-white border border-[var(--color-border)] rounded-xl max-w-lg w-full p-6 space-y-4 shadow-lg my-8">
        <h3 class="text-xl font-bold text-[var(--color-text)]">
          {{ editingGroup ? 'ပြင်ဆင်ရန်' : 'Modifier အုပ်စု အသစ်ထည့်ရန်' }}
        </h3>

        <div>
          <label class="block mb-2 text-sm font-medium text-[var(--color-text-muted)]">အမည်</label>
          <input
            v-model="form.name"
            type="text"
            class="glass-input w-full px-4 py-2 rounded-xl"
            placeholder="ဥပမာ: အရွယ်အစား"
            required
          />
        </div>

        <div>
          <label class="block mb-2 text-sm font-medium text-[var(--color-text-muted)]">ဖော်ပြချက် (ရွေးချယ်နိုင်)</label>
          <input
            v-model="form.description"
            type="text"
            class="glass-input w-full px-4 py-2 rounded-xl"
            placeholder=""
          />
        </div>

        <div class="flex items-center gap-4">
          <label class="flex items-center gap-2">
            <input v-model="form.is_required" type="checkbox" class="rounded border-[var(--color-border)]" />
            <span class="text-sm text-[var(--color-text)]">ရွေးရမည်</span>
          </label>
          <div class="flex items-center gap-2">
            <label class="text-sm text-[var(--color-text-muted)]">အများဆုံး ရွေးချယ်မှု</label>
            <input
              v-model.number="form.max_selections"
              type="number"
              min="1"
              class="glass-input w-20 px-2 py-1 rounded-lg text-center"
            />
          </div>
        </div>

        <div class="flex items-center gap-2">
          <input v-model="form.is_active" type="checkbox" class="rounded border-[var(--color-border)]" />
          <label class="text-sm font-medium text-[var(--color-text)]">အသက်သွင်းထား</label>
        </div>

        <div>
          <div class="flex justify-between items-center mb-2">
            <label class="text-sm font-medium text-[var(--color-text-muted)]">ရွေးချယ်စရာများ</label>
            <button
              type="button"
              @click="addOption"
              class="text-sm text-[var(--color-primary)] font-bold hover:underline"
            >
              + ထပ်ထည့်ရန်
            </button>
          </div>
          <div class="space-y-2 max-h-48 overflow-y-auto">
            <div
              v-for="(opt, idx) in form.options"
              :key="idx"
              class="flex gap-2 items-center p-2 rounded-lg bg-[var(--color-bg-light)] border border-[var(--color-border)]"
            >
              <input
                v-model="opt.name"
                type="text"
                class="glass-input flex-1 px-3 py-1.5 rounded-lg text-sm"
                placeholder="အမည်"
              />
              <input
                v-model.number="opt.price_adjustment"
                type="number"
                step="0.01"
                class="glass-input w-24 px-2 py-1.5 rounded-lg text-sm text-right"
                placeholder="+ MMK"
              />
              <span class="text-xs text-[var(--color-text-muted)] w-8">MMK</span>
              <button
                type="button"
                @click="removeOption(idx)"
                class="p-1 rounded text-rose-600 hover:bg-rose-50"
              >
                <Trash2 class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        <div class="flex gap-3 pt-4">
          <button
            @click="saveGroup"
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
import { Layers, Plus, Edit, Trash2 } from 'lucide-vue-next'
import api from '@/services/api'

const groups = ref([])
const loading = ref(false)
const saving = ref(false)
const showModal = ref(false)
const editingGroup = ref(null)

const form = ref({
  name: '',
  description: '',
  is_required: false,
  max_selections: 1,
  is_active: true,
  options: [{ name: '', price_adjustment: 0 }],
})

const fetchGroups = async () => {
  loading.value = true
  try {
    const res = await api.get('modifier-groups/')
    groups.value = res.data.results ?? res.data ?? []
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const openAddModal = () => {
  editingGroup.value = null
  form.value = {
    name: '',
    description: '',
    is_required: false,
    max_selections: 1,
    is_active: true,
    options: [{ name: '', price_adjustment: 0 }],
  }
  showModal.value = true
}

const addOption = () => {
  form.value.options.push({ name: '', price_adjustment: 0 })
}

const removeOption = (idx) => {
  form.value.options.splice(idx, 1)
  if (form.value.options.length === 0) form.value.options.push({ name: '', price_adjustment: 0 })
}

const editGroup = (group) => {
  editingGroup.value = group
  const opts = (group.options || []).length ? group.options.map(o => ({ name: o.name, price_adjustment: o.price_adjustment })) : [{ name: '', price_adjustment: 0 }]
  form.value = {
    name: group.name,
    description: group.description || '',
    is_required: group.is_required || false,
    max_selections: group.max_selections || 1,
    is_active: group.is_active,
    options: opts,
  }
  showModal.value = true
}

const saveGroup = async () => {
  if (!form.value.name.trim()) {
    alert('ကျေးဇူးပြု၍ အုပ်စု အမည် ဖြည့်သွင်းပါ။')
    return
  }

  const options = form.value.options
    .filter(o => (o.name || '').trim())
    .map((o, i) => ({ name: (o.name || '').trim(), price_adjustment: Number(o.price_adjustment) || 0, display_order: i, is_active: true }))
  if (options.length === 0) {
    alert('ရွေးချယ်စရာ အနည်းဆုံး တစ်ခု ထည့်ပါ။')
    return
  }

  saving.value = true
  try {
    const payload = {
      name: form.value.name.trim(),
      description: form.value.description.trim() || '',
      is_required: form.value.is_required,
      max_selections: form.value.max_selections,
      is_active: form.value.is_active,
      options,
    }
    if (editingGroup.value) {
      await api.patch(`modifier-groups/${editingGroup.value.id}/`, payload)
    } else {
      await api.post('modifier-groups/', payload)
    }
    await fetchGroups()
    closeModal()
    alert('သိမ်းဆည်းပြီးပါပြီ။')
  } catch (error) {
    console.error(error)
    alert('သိမ်းဆည်းခြင်း မအောင်မြင်ပါ။ ' + (error.response?.data?.detail || error.response?.data?.error || error.message))
  } finally {
    saving.value = false
  }
}

const deleteGroup = async (id) => {
  if (!confirm('ဤ Modifier အုပ်စုကို ဖျက်ရန် သေချာပါသလား?')) return
  try {
    await api.delete(`modifier-groups/${id}/`)
    await fetchGroups()
    alert('ဖျက်ပြီးပါပြီ။')
  } catch (error) {
    console.error(error)
    alert('ဖျက်ခြင်း မအောင်မြင်ပါ။ ' + (error.response?.data?.detail || error.message))
  }
}

const closeModal = () => {
  showModal.value = false
  editingGroup.value = null
}

onMounted(() => {
  fetchGroups()
})
</script>
