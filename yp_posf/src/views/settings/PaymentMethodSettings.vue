<template>
  <div class="bg-white border border-[var(--color-border)] rounded-xl p-6">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-lg font-bold text-[#1a1a1a] flex items-center gap-2">
        <DollarSign class="w-5 h-5 text-emerald-600" />
        ငွေပေးချေမှု နည်းလမ်းများ
      </h2>
      <button
        v-if="!readOnly"
        @click="openAddModal"
        class="px-4 py-2 rounded-xl bg-emerald-500 text-white font-bold text-sm hover:bg-emerald-600 transition-all flex items-center gap-2"
      >
        <Plus class="w-4 h-4" />
        ထည့်ရန်
      </button>
    </div>

    <div v-if="loading" class="text-center py-8 text-[#6b7280] text-base">Loading...</div>
    
    <div v-else class="space-y-3">
      <div
        v-for="pm in paymentMethods"
        :key="pm.id"
        class="p-4 bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl hover:bg-[#f3f4f6] transition-all"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="flex items-center gap-3 mb-2">
              <h3 class="font-bold text-[#1a1a1a]">{{ pm.name }}</h3>
              <span
                :class="pm.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-gray-100 text-gray-600'"
                class="px-2 py-1 rounded text-xs font-bold"
              >
                {{ pm.is_active ? 'Active' : 'Inactive' }}
              </span>
            </div>
            <div v-if="pm.account_name" class="text-sm text-[#4b5563] mb-1">
              Account: {{ pm.account_name }}
            </div>
            <div v-if="pm.account_number" class="text-sm text-[#4b5563] mb-2">
              Number: {{ pm.account_number }}
            </div>
            <div v-if="pm.qr_code_url" class="mt-3">
              <img :src="pm.qr_code_url" alt="QR Code" class="w-32 h-32 object-contain bg-white rounded-lg p-2" />
            </div>
          </div>
          <div v-if="!readOnly" class="flex items-center gap-2 ml-4">
            <button
              @click="editPaymentMethod(pm)"
              class="text-sky-600 hover:text-sky-700"
            >
              <Edit class="w-4 h-4" />
            </button>
            <button
              @click="toggleActive(pm)"
              class="text-amber-600 hover:text-amber-700"
            >
              <Power class="w-4 h-4" />
            </button>
            <button
              @click="deletePaymentMethod(pm.id)"
              class="text-rose-600 hover:text-rose-700"
            >
              <Trash2 class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
      
      <div v-if="paymentMethods.length === 0" class="text-center py-8 text-[#6b7280] text-base">
        Payment method မရှိပါ။
      </div>
    </div>

    <!-- Add/Edit Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white border border-[var(--color-border)] rounded-xl max-w-md w-full p-6 space-y-4 shadow-lg">
        <h3 class="text-xl font-bold text-[#1a1a1a]">
          {{ editingPaymentMethod ? 'ပြင်ဆင်ရန်' : 'အသစ်ထည့်ရန်' }}
        </h3>
        
        <div>
          <label class="block mb-2 text-sm font-medium text-[#374151]">အမည်</label>
          <input
            v-model="form.name"
            type="text"
            class="glass-input w-full px-4 py-2"
            placeholder="KPay, Wave Pay, AYA Pay, Cash"
            required
          />
        </div>

        <div>
          <label class="block mb-2 text-sm font-medium text-[#374151]">အကောင့်အမည်</label>
          <input
            v-model="form.account_name"
            type="text"
            class="glass-input w-full px-4 py-2"
            placeholder="Account holder name"
          />
        </div>

        <div>
          <label class="block mb-2 text-sm font-medium text-[#374151]">အကောင့်နံပါတ်/ဖုန်းနံပါတ်</label>
          <input
            v-model="form.account_number"
            type="text"
            class="glass-input w-full px-4 py-2"
            placeholder="09xxxxxxxxx"
          />
        </div>

        <div>
          <label class="block mb-2 text-sm font-medium text-[#374151]">QR Code ပုံ</label>
          <input
            type="file"
            accept="image/*"
            @change="handleQRCodeFile"
            ref="qrCodeInput"
            class="hidden"
          />
          <button
            @click="$refs.qrCodeInput?.click()"
            class="w-full py-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] text-[#1a1a1a] text-sm font-bold hover:bg-[#f3f4f6] mb-2"
          >
            QR Code ရွေးရန်
          </button>
          <div v-if="form.qrCodePreview" class="mt-2">
            <img :src="form.qrCodePreview" alt="QR Preview" class="w-32 h-32 object-contain bg-white rounded-lg p-2 mx-auto" />
          </div>
          <div v-else-if="editingPaymentMethod?.qr_code_url" class="mt-2">
            <img :src="editingPaymentMethod.qr_code_url" alt="Current QR" class="w-32 h-32 object-contain bg-white rounded-lg p-2 mx-auto" />
          </div>
        </div>

        <div>
          <label class="block mb-2 text-sm font-medium text-[#374151]">ပြသရန် အစဉ်</label>
          <input
            v-model.number="form.display_order"
            type="number"
            class="glass-input w-full px-4 py-2"
            placeholder="0"
          />
        </div>

        <div class="flex items-center gap-2">
          <input
            v-model="form.is_active"
            type="checkbox"
            id="is_active"
            class="w-4 h-4"
          />
          <label for="is_active" class="text-sm font-medium text-[#1a1a1a]">Active</label>
        </div>

        <div class="flex gap-3 pt-4">
          <button
            @click="savePaymentMethod"
            :disabled="saving"
            class="flex-1 px-4 py-2 rounded-xl bg-emerald-500 text-white font-bold hover:bg-emerald-600 transition-all disabled:opacity-70"
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
import { DollarSign, Plus, Edit, Trash2, Power } from 'lucide-vue-next'
import api from '@/services/api'

defineProps({ readOnly: { type: Boolean, default: false } })
const paymentMethods = ref([])
const loading = ref(false)
const saving = ref(false)
const showModal = ref(false)
const editingPaymentMethod = ref(null)

const form = ref({
  name: '',
  account_name: '',
  account_number: '',
  qr_code_image: null,
  qrCodePreview: null,
  display_order: 0,
  is_active: true,
})

const fetchPaymentMethods = async () => {
  loading.value = true
  try {
    // api service က auto token injection လုပ်ပေးတယ်
    const res = await api.get('payment-methods/')
    paymentMethods.value = res.data.results ?? res.data ?? []
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const openAddModal = () => {
  editingPaymentMethod.value = null
  form.value = {
    name: '',
    account_name: '',
    account_number: '',
    qr_code_image: null,
    qrCodePreview: null,
    display_order: 0,
    is_active: true,
  }
  showModal.value = true
}

const editPaymentMethod = (pm) => {
  editingPaymentMethod.value = pm
  form.value = {
    name: pm.name,
    account_name: pm.account_name || '',
    account_number: pm.account_number || '',
    qr_code_image: null,
    qrCodePreview: null,
    display_order: pm.display_order || 0,
    is_active: pm.is_active,
  }
  showModal.value = true
}

const handleQRCodeFile = (event) => {
  const file = event.target.files?.[0]
  if (file) {
    if (file.size > 5 * 1024 * 1024) {
      alert('File size must be less than 5MB')
      return
    }
    if (!file.type.startsWith('image/')) {
      alert('Only image files are allowed')
      return
    }
    form.value.qr_code_image = file
    form.value.qrCodePreview = URL.createObjectURL(file)
  }
}

const savePaymentMethod = async () => {
  if (!form.value.name.trim()) {
    alert('ကျေးဇူးပြု၍ အမည် ဖြည့်သွင်းပါ။')
    return
  }

  saving.value = true
  try {
    const formData = new FormData()
    formData.append('name', form.value.name)
    if (form.value.account_name) formData.append('account_name', form.value.account_name)
    if (form.value.account_number) formData.append('account_number', form.value.account_number)
    if (form.value.qr_code_image) formData.append('qr_code_image', form.value.qr_code_image)
    formData.append('display_order', form.value.display_order)
    formData.append('is_active', form.value.is_active)

    // api service က auto token injection လုပ်ပေးတယ်
    if (editingPaymentMethod.value) {
      await api.put(`payment-methods/${editingPaymentMethod.value.id}/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    } else {
      await api.post('payment-methods/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    }
    
    await fetchPaymentMethods()
    closeModal()
    alert('သိမ်းဆည်းပြီးပါပြီ။')
  } catch (error) {
    console.error(error)
    alert('သိမ်းဆည်းခြင်း မအောင်မြင်ပါ။ ' + (error.response?.data?.error || error.message))
  } finally {
    saving.value = false
  }
}

const toggleActive = async (pm) => {
  try {
    // api service က auto token injection လုပ်ပေးတယ်
    await api.patch(`payment-methods/${pm.id}/`, { is_active: !pm.is_active })
    await fetchPaymentMethods()
  } catch (error) {
    console.error(error)
    alert('Update failed')
  }
}

const deletePaymentMethod = async (id) => {
  if (!confirm('ဤ payment method ကို ဖျက်ရန် သေချာပါသလား?')) return
  
  try {
    // api service က auto token injection လုပ်ပေးတယ်
    await api.delete(`payment-methods/${id}/`)
    await fetchPaymentMethods()
    alert('ဖျက်ပြီးပါပြီ။')
  } catch (error) {
    console.error(error)
    alert('ဖျက်ခြင်း မအောင်မြင်ပါ။')
  }
}

const closeModal = () => {
  showModal.value = false
  editingPaymentMethod.value = null
  form.value.qrCodePreview = null
}

onMounted(() => {
  fetchPaymentMethods()
})
</script>
