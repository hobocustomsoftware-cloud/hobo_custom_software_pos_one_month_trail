<template>
  <div class="bg-white max-w-4xl w-full p-6 space-y-6 max-h-[90vh] overflow-y-auto custom-scrollbar rounded-xl border border-[var(--color-border)] shadow-xl" style="gap: var(--fluid-gap);">
    <div class="flex justify-between items-start">
      <h2 class="text-fluid-xl font-black uppercase tracking-tight text-[#1a1a1a]">Installation Details</h2>
      <button
        @click="$emit('close')"
        class="btn-secondary px-4 py-2 interactive"
      >
        ✕ Close
      </button>
    </div>

    <div v-if="loading" class="text-center text-[#4b5563]">Loading...</div>
    <div v-else-if="installation">
      <!-- Basic Info -->
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block mb-1 text-sm font-medium text-[#374151]">Installation No.</label>
          <p class="text-[#1a1a1a] font-bold">{{ installation.installation_no }}</p>
        </div>
        <div>
          <label class="block mb-1 text-sm font-medium text-[#374151]">Invoice</label>
          <p class="text-[#1a1a1a]">{{ installation.sale_transaction_invoice }}</p>
        </div>
        <div>
          <label class="block mb-1 text-sm font-medium text-[#374151]">Customer</label>
          <p class="text-[#1a1a1a]">{{ installation.customer_name }}</p>
          <p class="text-[#6b7280] text-sm">{{ installation.customer_phone }}</p>
        </div>
        <div>
          <label class="block mb-1 text-sm font-medium text-[#374151]">Status</label>
          <span :class="getStatusClass(installation.status)" class="px-3 py-1 rounded font-bold">
            {{ getStatusText(installation.status) }}
          </span>
        </div>
      </div>

      <!-- Installation Details -->
      <div>
        <label class="block mb-1 text-sm font-medium text-[#374151]">Installation Address</label>
        <p class="text-[#1a1a1a]">{{ installation.installation_address }}</p>
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block mb-1 text-sm font-medium text-[#374151]">Installation Date</label>
          <p class="text-[#1a1a1a]">{{ formatDate(installation.installation_date) }}</p>
        </div>
        <div>
          <label class="block mb-1 text-sm font-medium text-[#374151]">Estimated Completion</label>
          <p class="text-[#1a1a1a]">{{ formatDate(installation.estimated_completion_date) || '—' }}</p>
        </div>
        <div>
          <label class="block mb-1 text-sm font-medium text-[#374151]">သွားတိုင်းရမည့်ရက်</label>
          <input
            v-model="updateForm.site_visit_date"
            type="date"
            class="glass-input w-full px-4 py-2"
            @change="updateField('site_visit_date', updateForm.site_visit_date || null)"
          />
        </div>
      </div>

      <!-- Technician -->
      <div>
        <label class="block mb-2 text-sm font-medium text-[#374151]">Technician</label>
        <select
          v-model="updateForm.technician"
          class="glass-input w-full px-4 py-2"
          @change="updateField('technician', updateForm.technician)"
        >
          <option value="">Select Technician</option>
          <option v-for="tech in technicians" :key="tech.id" :value="tech.id">
            {{ tech.username }} ({{ tech.first_name }} {{ tech.last_name }})
          </option>
        </select>
      </div>

      <!-- Status Update -->
      <div>
        <label class="block mb-2 text-sm font-medium text-[#374151]">Update Status</label>
        <div class="flex gap-2">
          <select
            v-model="updateForm.status"
            class="glass-input flex-1 px-4 py-2"
            @change="updateStatus"
          >
            <option value="pending">Pending</option>
            <option value="site_visit">သွားတိုင်းရမည် (Site visit)</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="signed_off">Signed Off</option>
            <option value="cancelled">Cancelled</option>
          </select>
          <button
            @click="updateStatus"
            class="btn-primary px-4 py-2 interactive"
          >
            Update
          </button>
        </div>
      </div>

      <!-- Description & Notes -->
      <div>
        <label class="block mb-2 text-sm font-medium text-[#374151]">Description</label>
        <textarea
          v-model="updateForm.description"
          rows="3"
          class="glass-input w-full px-4 py-2"
          @blur="updateField('description', updateForm.description)"
        />
      </div>

      <div>
        <label class="block mb-2 text-sm font-medium text-[#374151]">Notes</label>
        <textarea
          v-model="updateForm.notes"
          rows="3"
          class="glass-input w-full px-4 py-2"
          @blur="updateField('notes', updateForm.notes)"
        />
      </div>

      <!-- Signature Capture -->
      <div v-if="installation.status === 'completed'">
        <label class="block mb-2 text-sm font-medium text-[#374151]">Customer Signature</label>
        <div v-if="installation.customer_signature_url" class="mb-4">
          <img
            :src="installation.customer_signature_url"
            alt="Customer Signature"
            class="max-w-md border border-[var(--color-border)] rounded"
          />
        </div>
        <div v-else>
          <SignatureCapture
            @signature-captured="uploadSignature"
            :disabled="installation.status === 'signed_off'"
          />
        </div>
      </div>

      <!-- Status History -->
      <div v-if="installation.status_history && installation.status_history.length > 0">
        <label class="block mb-2 text-sm font-medium text-[#374151]">Status History</label>
        <div class="space-y-2">
          <div
            v-for="history in installation.status_history"
            :key="history.id"
            class="bg-[var(--color-bg-card)] p-3 text-sm rounded-xl border border-[var(--color-border)]"
          >
            <div class="flex justify-between">
              <span class="text-[#1a1a1a]">
                {{ history.old_status || '—' }} → {{ history.new_status }}
              </span>
              <span class="text-[#6b7280]">{{ formatDateTime(history.created_at) }}</span>
            </div>
            <p v-if="history.notes" class="text-[#4b5563] mt-1">{{ history.notes }}</p>
            <p class="text-[#6b7280] text-xs">By: {{ history.updated_by_username }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import api from '@/services/api'
import SignatureCapture from './SignatureCapture.vue'

const props = defineProps({
  installation: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['close', 'updated'])

const loading = ref(false)
const technicians = ref([])
const updateForm = ref({
  technician: props.installation?.technician || '',
  status: props.installation?.status || 'pending',
  site_visit_date: props.installation?.site_visit_date || '',
  description: props.installation?.description || '',
  notes: props.installation?.notes || '',
})

const toDateInputValue = (v) => {
  if (!v) return ''
  const s = typeof v === 'string' ? v : (v.toISOString && v.toISOString())
  return s ? s.slice(0, 10) : ''
}

watch(
  () => props.installation,
  (newVal) => {
    if (newVal) {
      updateForm.value = {
        technician: newVal.technician || '',
        status: newVal.status || 'pending',
        site_visit_date: toDateInputValue(newVal.site_visit_date),
        description: newVal.description || '',
        notes: newVal.notes || '',
      }
    }
  },
  { immediate: true }
)

const fetchTechnicians = async () => {
  try {
    // api service က auto token injection လုပ်ပေးတယ်
    const res = await api.get('core/employees/')
    technicians.value = (res.data.results ?? res.data ?? []).filter(
      (emp) => emp.role_name && emp.role_name.toLowerCase().includes('technician')
    )
  } catch (error) {
    console.error(error)
  }
}

const updateField = async (field, value) => {
  try {
    // api service က auto token injection လုပ်ပေးတယ်
    await api.patch(`installation/jobs/${props.installation.id}/`, { [field]: value })
    emit('updated')
  } catch (error) {
    console.error(error)
    alert('Update မအောင်မြင်ပါ။')
  }
}

const updateStatus = async () => {
  try {
    // api service က auto token injection လုပ်ပေးတယ်
    await api.post(`installation/jobs/${props.installation.id}/update-status/`, {
      status: updateForm.value.status,
      notes: updateForm.value.notes,
    })
    emit('updated')
    alert('Status updated successfully')
  } catch (error) {
    console.error(error)
    alert('Status update မအောင်မြင်ပါ။')
  }
}

const uploadSignature = async (signatureFile) => {
  try {
    const formData = new FormData()
    formData.append('signature', signatureFile)
    // api service က auto token injection လုပ်ပေးတယ်
    await api.post(`installation/jobs/${props.installation.id}/upload-signature/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    emit('updated')
    alert('Signature uploaded successfully')
  } catch (error) {
    console.error(error)
    alert('Signature upload မအောင်မြင်ပါ။')
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('my-MM')
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleString('my-MM')
}

const getStatusClass = (status) => {
  const classes = {
    pending: 'bg-yellow-500/20 text-yellow-400',
    site_visit: 'bg-amber-500/20 text-amber-400',
    in_progress: 'bg-blue-500/20 text-blue-400',
    completed: 'bg-green-500/20 text-green-400',
    signed_off: 'bg-purple-500/20 text-purple-400',
    cancelled: 'bg-red-500/20 text-red-400',
  }
  return classes[status] || 'bg-gray-500/20 text-gray-400'
}

const getStatusText = (status) => {
  const texts = {
    pending: 'Pending',
    site_visit: 'သွားတိုင်းရမည်',
    in_progress: 'In Progress',
    completed: 'Completed',
    signed_off: 'Signed Off',
    cancelled: 'Cancelled',
  }
  return texts[status] || status
}

onMounted(() => {
  fetchTechnicians()
})
</script>
