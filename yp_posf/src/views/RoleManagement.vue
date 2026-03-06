<template>
  <div class="layout-container space-y-6 bg-[#f4f4f4] min-h-full" style="gap: var(--fluid-gap);">
    <div class="flex flex-wrap justify-between items-center" style="gap: var(--fluid-gap);">
      <h1 class="text-fluid-xl font-black uppercase tracking-tight text-[#1a1a1a]">Role များ</h1>
      <button
        @click="openAddModal"
        class="btn-primary px-6 py-2.5 flex items-center gap-2 interactive"
      >
        <span>+ အသစ်ထည့်မယ်</span>
      </button>
    </div>

    <div class="bg-white rounded-xl border border-[var(--color-border)] shadow-sm overflow-hidden">
      <div v-if="loading" class="p-20 text-center text-[#4b5563] font-semibold">
        <div class="animate-pulse">Loading Roles...</div>
      </div>

      <div v-else class="overflow-x-auto custom-scrollbar">
        <table class="w-full">
          <thead class="bg-[var(--color-bg-card)] border-b border-[var(--color-border)]">
            <tr>
              <th class="p-4 text-left text-xs font-bold text-[#6b7280] uppercase">Role အမည်</th>
              <th class="p-4 text-left text-xs font-bold text-[#6b7280] uppercase">အကြောင်းအရာ</th>
              <th class="p-4 text-right text-xs font-bold text-[#6b7280] uppercase">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[var(--color-border)]">
            <tr v-for="r in roles" :key="r.id" class="interactive hover:bg-[var(--color-bg-card)]">
              <td class="p-4 font-semibold text-[#1a1a1a] uppercase text-fluid-sm">{{ r.name }}</td>
              <td class="p-4 text-fluid-sm text-[#4b5563]">{{ r.description || '—' }}</td>
              <td class="p-4 text-right">
                <div class="flex items-center justify-end gap-2">
                  <button
                    @click="openEditModal(r)"
                    class="text-sky-600 font-semibold text-fluid-sm hover:text-sky-700 hover:underline transition-colors interactive"
                  >
                    Edit
                  </button>
                  <button
                    @click="deleteRole(r)"
                    class="text-rose-600 font-semibold text-fluid-sm hover:text-rose-700 hover:underline transition-colors interactive"
                  >
                    Delete
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="showModal" class="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <div
        class="absolute inset-0 bg-black/60 backdrop-blur-sm"
        @click="showModal = false"
      ></div>
      <div class="bg-white w-full max-w-md p-8 relative z-10 rounded-xl border border-[var(--color-border)] shadow-xl">
        <h3 class="text-fluid-xl font-black text-[#1a1a1a] mb-6 uppercase tracking-tight">
          {{ isEdit ? 'Role ပြင်မယ်' : 'Role အသစ်ထည့်မယ်' }}
        </h3>

        <form @submit.prevent="saveRole" class="space-y-5" style="gap: var(--fluid-gap);">
          <div>
            <label class="block mb-2 text-sm font-medium text-[#374151]">Role အမည်</label>
            <input
              v-model="form.name"
              type="text"
              required
              placeholder="ဥပမာ owner, manager"
              class="glass-input w-full px-4 py-3 rounded-xl"
            />
          </div>
          <div>
            <label class="block mb-2 text-sm font-medium text-[#374151]">အကြောင်းအရာ</label>
            <textarea
              v-model="form.description"
              rows="2"
              placeholder="ရွေးချယ်နိုင်သည်"
              class="glass-input w-full px-4 py-3 rounded-xl resize-none"
            />
          </div>
          <div class="flex gap-4 pt-4">
            <button
              type="button"
              @click="showModal = false"
              class="flex-1 btn-secondary py-3 interactive"
            >
              ပယ်ဖျက်
            </button>
            <button
              type="submit"
              :disabled="submitting"
              class="flex-1 btn-primary py-3 interactive disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ submitting ? 'သိမ်းနေပါ...' : 'သိမ်းမယ်' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

const roles = ref([])
const loading = ref(false)
const showModal = ref(false)
const submitting = ref(false)
const isEdit = ref(false)
const currentRoleId = ref(null)
const form = ref({ name: '', description: '' })

const fetchRoles = async () => {
  try {
    const res = await api.get('core/roles/')
    roles.value = res.data
  } catch (err) {
    console.error('Roles Error:', err)
  }
}

const openAddModal = () => {
  isEdit.value = false
  form.value = { name: '', description: '' }
  showModal.value = true
}

const openEditModal = (r) => {
  isEdit.value = true
  currentRoleId.value = r.id
  form.value = { name: r.name, description: r.description || '' }
  showModal.value = true
}

const saveRole = async () => {
  submitting.value = true
  try {
    if (isEdit.value) {
      await api.patch(`core/roles/${currentRoleId.value}/`, form.value)
    } else {
      await api.post('core/roles/', form.value)
    }
    showModal.value = false
    await fetchRoles()
    alert('အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ။')
  } catch (err) {
    const msg = err.response?.data?.name?.[0] || err.response?.data?.detail || 'သိမ်း၍မရပါ။'
    alert(msg)
  } finally {
    submitting.value = false
  }
}

const deleteRole = async (r) => {
  if (!confirm(`"${r.name}" Role ကို ဖျက်မှာ သေချာပါသလား?`)) return
  try {
    await api.delete(`core/roles/${r.id}/`)
    await fetchRoles()
    alert('ဖျက်ပြီးပါပြီ။')
  } catch (err) {
    alert(err.response?.data?.detail || 'ဖျက်၍မရပါ။')
  }
}

onMounted(() => {
  loading.value = true
  fetchRoles().finally(() => { loading.value = false })
})
</script>
