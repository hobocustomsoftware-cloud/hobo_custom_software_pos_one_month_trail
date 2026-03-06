<template>
  <div class="bg-white border border-[var(--color-border)] rounded-xl p-6">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-lg font-bold text-[#1a1a1a] flex items-center gap-2">
        <Tag class="w-5 h-5 text-blue-600" />
        ကုန်ကျစရိတ် အမျိုးအစားများ
      </h2>
      <button
        v-if="!readOnly"
        @click="openAddModal"
        class="px-4 py-2 rounded-xl bg-blue-500 text-white font-bold text-sm hover:bg-blue-600 transition-all flex items-center gap-2"
      >
        <Plus class="w-4 h-4" />
        ထည့်ရန်
      </button>
    </div>

    <div v-if="loading" class="text-center py-8 text-[#6b7280] text-base">Loading...</div>
    
    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-3">
      <div
        v-for="cat in categories"
        :key="cat.id"
        class="p-4 bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl hover:bg-[#f3f4f6] transition-all"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <h3 class="font-bold text-[#1a1a1a] mb-1">{{ cat.name }}</h3>
            <p v-if="cat.description" class="text-sm text-[#4b5563]">{{ cat.description }}</p>
          </div>
          <div v-if="!readOnly" class="flex items-center gap-2 ml-4">
            <button
              @click="editCategory(cat)"
              class="text-sky-600 hover:text-sky-700"
            >
              <Edit class="w-4 h-4" />
            </button>
            <button
              @click="deleteCategory(cat.id)"
              class="text-rose-600 hover:text-rose-700"
            >
              <Trash2 class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
      
      <div v-if="categories.length === 0" class="col-span-2 text-center py-8 text-[#6b7280] text-base">
        Category မရှိပါ။
      </div>
    </div>

    <!-- Add/Edit Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white border border-[var(--color-border)] rounded-xl max-w-md w-full p-6 space-y-4 shadow-lg">
        <h3 class="text-xl font-bold text-[#1a1a1a]">
          {{ editingCategory ? 'ပြင်ဆင်ရန်' : 'အသစ်ထည့်ရန်' }}
        </h3>
        
        <div>
          <label class="block mb-2 text-sm font-medium text-[#374151]">အမည်</label>
          <input
            v-model="form.name"
            type="text"
            class="glass-input w-full px-4 py-2"
            placeholder="ဥပမာ: အငှားချ, လျှပ်စစ်မီး"
            required
          />
        </div>

        <div>
          <label class="block mb-2 text-sm font-medium text-[#374151]">ဖော်ပြချက်</label>
          <textarea
            v-model="form.description"
            rows="3"
            class="glass-input w-full px-4 py-2"
            placeholder="ရွေးချယ်နိုင်သည်"
          />
        </div>

        <div class="flex gap-3 pt-4">
          <button
            @click="saveCategory"
            :disabled="saving"
            class="flex-1 px-4 py-2 rounded-xl bg-blue-500 text-white font-bold hover:bg-blue-600 transition-all disabled:opacity-70"
          >
            {{ saving ? 'သိမ်းနေသည်...' : 'သိမ်းဆည်းရန်' }}
          </button>
          <button
            @click="closeModal"
            class="flex-1 px-4 py-2 rounded-xl border border-[var(--color-border)] bg-white text-[#1a1a1a] font-bold hover:bg-[#f3f4f6] transition-all"
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
import { Tag, Plus, Edit, Trash2 } from 'lucide-vue-next'
import api from '@/services/api'

defineProps({ readOnly: { type: Boolean, default: false } })
const categories = ref([])
const loading = ref(false)
const saving = ref(false)
const showModal = ref(false)
const editingCategory = ref(null)

const form = ref({
  name: '',
  description: '',
})

const fetchCategories = async () => {
  loading.value = true
  try {
    // api service က auto token injection လုပ်ပေးတယ်
    const res = await api.get('accounting/expense-categories/')
    categories.value = res.data.results ?? res.data ?? []
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const openAddModal = () => {
  editingCategory.value = null
  form.value = { name: '', description: '' }
  showModal.value = true
}

const editCategory = (cat) => {
  editingCategory.value = cat
  form.value = {
    name: cat.name,
    description: cat.description || '',
  }
  showModal.value = true
}

const saveCategory = async () => {
  if (!form.value.name.trim()) {
    alert('ကျေးဇူးပြု၍ အမည် ဖြည့်သွင်းပါ။')
    return
  }

  saving.value = true
  try {
    // api service က auto token injection လုပ်ပေးတယ်
    if (editingCategory.value) {
      await api.put(`accounting/expense-categories/${editingCategory.value.id}/`, form.value)
    } else {
      await api.post('accounting/expense-categories/', form.value)
    }
    
    await fetchCategories()
    closeModal()
    alert('သိမ်းဆည်းပြီးပါပြီ။')
  } catch (error) {
    console.error(error)
    alert('သိမ်းဆည်းခြင်း မအောင်မြင်ပါ။ ' + (error.response?.data?.error || error.message))
  } finally {
    saving.value = false
  }
}

const deleteCategory = async (id) => {
  if (!confirm('ဤ category ကို ဖျက်ရန် သေချာပါသလား?')) return
  
  try {
    // api service က auto token injection လုပ်ပေးတယ်
    await api.delete(`accounting/expense-categories/${id}/`)
    await fetchCategories()
    alert('ဖျက်ပြီးပါပြီ။')
  } catch (error) {
    console.error(error)
    alert('ဖျက်ခြင်း မအောင်မြင်ပါ။ ' + (error.response?.data?.error || error.message))
  }
}

const closeModal = () => {
  showModal.value = false
  editingCategory.value = null
}

onMounted(() => {
  fetchCategories()
})
</script>
