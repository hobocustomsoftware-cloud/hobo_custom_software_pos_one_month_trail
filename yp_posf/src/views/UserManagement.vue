<template>
  <div class="layout-container space-y-6 bg-[#f4f4f4] min-h-full" style="gap: var(--fluid-gap);">
    <div class="flex flex-wrap justify-between items-center" style="gap: var(--fluid-gap);">
      <h1 class="text-fluid-xl font-black uppercase tracking-tight text-[#1a1a1a]">User Management</h1>
      <button
        @click="openAddModal"
        class="btn-primary px-6 py-2.5 flex items-center gap-2 interactive"
      >
        <span>+ ADD NEW USER</span>
      </button>
    </div>

    <div class="bg-white rounded-xl border border-[var(--color-border)] shadow-sm overflow-hidden">
      <div v-if="loading" class="p-20 text-center text-[#4b5563] font-semibold">
        <div class="animate-pulse">Loading Users & Roles...</div>
      </div>

      <div v-else class="overflow-x-auto custom-scrollbar">
        <table class="w-full">
          <thead class="bg-[var(--color-bg-card)] border-b border-[var(--color-border)]">
            <tr>
              <th class="p-4 text-left text-xs font-bold text-[#6b7280] uppercase">Username</th>
              <th class="p-4 text-left text-xs font-bold text-[#6b7280] uppercase">Role</th>
              <th class="p-4 text-right text-xs font-bold text-[#6b7280] uppercase">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[var(--color-border)]">
            <tr v-for="u in users" :key="u.id" class="interactive hover:bg-[var(--color-bg-card)]">
              <td class="p-4 font-semibold text-[#1a1a1a] uppercase text-fluid-sm">{{ u.username }}</td>
              <td class="p-4">
                <span class="px-3 py-1.5 bg-[var(--color-bg-card)] rounded-lg text-fluid-sm font-semibold uppercase border border-[var(--color-border)] text-[#374151]">
                  {{ getRoleDisplayName(u) }}
                </span>
              </td>
              <td class="p-4 text-right">
                <div class="flex items-center justify-end gap-1.5">
                  <button
                    type="button"
                    @click="openEditModal(u)"
                    class="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-blue-600 hover:bg-blue-50 font-semibold text-sm transition-colors"
                  >
                    <Pencil class="w-4 h-4 shrink-0" />
                    <span>Edit</span>
                  </button>
                  <button
                    type="button"
                    @click="deleteUser(u.id)"
                    class="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-red-600 hover:bg-red-50 font-semibold text-sm transition-colors"
                  >
                    <Trash2 class="w-4 h-4 shrink-0" />
                    <span>Delete</span>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Add/Edit User Modal: tabbed, mobile-responsive -->
    <Teleport to="body">
      <div v-if="showModal" class="fixed inset-0 z-[100] flex items-end sm:items-center justify-center p-0 sm:p-4">
        <div
          class="absolute inset-0 bg-black/60 backdrop-blur-sm"
          @click="showModal = false"
        ></div>
        <div
          class="bg-white w-full relative z-10 rounded-t-2xl sm:rounded-xl border border-[var(--color-border)] shadow-xl flex flex-col max-h-[92vh] sm:max-h-[88vh] sm:max-w-lg sm:min-w-[min(100%,28rem)]"
          role="dialog"
          aria-labelledby="user-modal-title"
        >
          <!-- Header -->
          <div class="shrink-0 px-4 sm:px-6 pt-5 sm:pt-6 pb-2 border-b border-[var(--color-border)]">
            <h3 id="user-modal-title" class="text-lg sm:text-fluid-xl font-black text-[#1a1a1a] uppercase tracking-tight">
              {{ isEdit ? 'Update User' : 'Add New User' }}
            </h3>
            <!-- Tabs -->
            <nav class="flex mt-4 gap-0 -mb-px" aria-label="Form sections">
              <button
                type="button"
                :class="[
                  'flex-1 min-w-0 py-3 px-2 sm:px-3 text-xs sm:text-sm font-semibold border-b-2 transition-colors interactive truncate',
                  activeTab === 0
                    ? 'border-[#aa0000] text-[#aa0000] bg-transparent'
                    : 'border-transparent text-[#6b7280] hover:text-[#374151] hover:border-[#d1d5db]'
                ]"
                @click="activeTab = 0"
              >
                Basic Info
              </button>
              <button
                type="button"
                :class="[
                  'flex-1 min-w-0 py-3 px-2 sm:px-3 text-xs sm:text-sm font-semibold border-b-2 transition-colors interactive truncate',
                  activeTab === 1
                    ? 'border-[#aa0000] text-[#aa0000] bg-transparent'
                    : 'border-transparent text-[#6b7280] hover:text-[#374151] hover:border-[#d1d5db]'
                ]"
                @click="activeTab = 1"
              >
                Permissions
              </button>
              <button
                type="button"
                :class="[
                  'flex-1 min-w-0 py-3 px-2 sm:px-3 text-xs sm:text-sm font-semibold border-b-2 transition-colors interactive truncate',
                  activeTab === 2
                    ? 'border-[#aa0000] text-[#aa0000] bg-transparent'
                    : 'border-transparent text-[#6b7280] hover:text-[#374151] hover:border-[#d1d5db]'
                ]"
                @click="activeTab = 2"
              >
                Assignment
              </button>
            </nav>
          </div>

          <form @submit.prevent="saveUser" class="flex flex-col flex-1 min-h-0">
            <!-- Tab panels: scrollable body -->
            <div class="flex-1 overflow-y-auto overscroll-contain px-4 sm:px-6 py-4 sm:py-5">
              <!-- Tab 1: Basic Info (Username, Phone, Email, Password) -->
              <div v-show="activeTab === 0" class="space-y-4">
                <div>
                  <label class="block mb-1.5 text-sm font-medium text-[#374151]">Username</label>
                  <input
                    v-model="form.username"
                    type="text"
                    required
                    class="glass-input w-full px-4 py-2.5 sm:py-3 rounded-xl text-base"
                    placeholder="ဝင်ရောက်ရန် သုံးမည့်အမည်"
                  />
                </div>
                <div>
                  <label class="block mb-1.5 text-sm font-medium text-[#374151]">ဖုန်းနံပါတ်</label>
                  <input
                    v-model="form.phone_number"
                    type="tel"
                    class="glass-input w-full px-4 py-2.5 sm:py-3 rounded-xl text-base"
                    placeholder="၀၉xxxxxxxx"
                  />
                </div>
                <div>
                  <label class="block mb-1.5 text-sm font-medium text-[#374151]">Email</label>
                  <input
                    v-model="form.email"
                    type="email"
                    class="glass-input w-full px-4 py-2.5 sm:py-3 rounded-xl text-base"
                    placeholder="you@example.com"
                  />
                </div>
                <div v-if="!isEdit">
                  <label class="block mb-1.5 text-sm font-medium text-[#374151]">Password</label>
                  <input
                    v-model="form.password"
                    type="password"
                    required
                    class="glass-input w-full px-4 py-2.5 sm:py-3 rounded-xl text-base"
                    placeholder="••••••••"
                  />
                </div>
              </div>

              <!-- Tab 2: Permissions (Role, Assignment type) -->
              <div v-show="activeTab === 1" class="space-y-4">
                <div>
                  <label class="block mb-1.5 text-sm font-medium text-[#374151]">Role</label>
                  <select
                    v-model="form.role"
                    required
                    class="glass-input w-full px-4 py-2.5 sm:py-3 rounded-xl appearance-none text-base"
                  >
                    <option value="" disabled>ရွေးချယ်ပါ</option>
                    <option v-for="r in roles" :key="r.id" :value="r.id">{{ r.name }}</option>
                  </select>
                </div>
                <div>
                  <label class="block mb-1.5 text-sm font-medium text-[#374151]">တာဝန်ချထားမှု အမျိုးအစား</label>
                  <select
                    v-model="form.assignment_type"
                    class="glass-input w-full px-4 py-2.5 sm:py-3 rounded-xl appearance-none text-base"
                  >
                    <option value="fixed">ပုံသေ (တစ်ဆိုင်တည်း)</option>
                    <option value="rotating">အလှည့်ကျ (ဆိုင်များကို လဲလှည့်သွားသည်)</option>
                  </select>
                </div>
                <p class="text-xs text-[#6b7280] mt-2">
                  Admin panel ဝင်ခွင့်သည် ရွေးထားသော Role အပေါ်တွင် မူတည်ပါသည်။
                </p>
              </div>

              <!-- Tab 3: Assignment (Primary outlet, Assigned locations) -->
              <div v-show="activeTab === 2" class="space-y-4">
                <div>
                  <label class="block mb-1.5 text-sm font-medium text-[#374151]">ပုံသေ ဆိုင် (Outlet)</label>
                  <select
                    v-model="form.primary_location"
                    class="glass-input w-full px-4 py-2.5 sm:py-3 rounded-xl appearance-none text-base"
                  >
                    <option :value="null">မရွေးပါ</option>
                    <option v-for="loc in saleLocations" :key="loc.id" :value="loc.id">{{ loc.name }}</option>
                  </select>
                </div>
                <div>
                  <label class="block mb-1.5 text-sm font-medium text-[#374151]">တာဝန်ကျ ဆိုင်များ</label>
                  <div class="flex flex-wrap gap-2 p-3 sm:p-4 bg-[var(--color-bg-card)] rounded-xl max-h-32 sm:max-h-28 overflow-y-auto custom-scrollbar border border-[var(--color-border)]">
                    <label
                      v-for="loc in saleLocations"
                      :key="loc.id"
                      class="flex items-center gap-2 cursor-pointer min-w-0"
                    >
                      <input
                        type="checkbox"
                        :value="loc.id"
                        v-model="form.assigned_locations"
                        class="rounded accent-[#aa0000] shrink-0"
                      />
                      <span class="text-sm text-[#374151] truncate">{{ loc.name }}</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>

            <!-- Footer: fixed ratio, safe area -->
            <div class="shrink-0 flex gap-3 sm:gap-4 p-4 sm:p-6 pt-3 sm:pt-4 border-t border-[var(--color-border)] bg-white">
              <button
                type="button"
                @click="showModal = false"
                class="flex-1 min-w-0 btn-secondary py-2.5 sm:py-3 text-sm sm:text-base interactive"
              >
                CANCEL
              </button>
              <button
                type="submit"
                :disabled="submitting"
                class="flex-1 min-w-0 btn-primary py-2.5 sm:py-3 text-sm sm:text-base interactive disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {{ submitting ? 'SAVING...' : 'CONFIRM' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Pencil, Trash2 } from 'lucide-vue-next'
const users = ref([])
const roles = ref([])
const saleLocations = ref([])
const loading = ref(false)
const showModal = ref(false)
const submitting = ref(false)
const isEdit = ref(false)
const currentUserId = ref(null)
const activeTab = ref(0)

const form = ref({ username: '', password: '', role: '', assignment_type: 'fixed', primary_location: null, assigned_locations: [] })

import api from '@/services/api'

const fetchRoles = async () => {
  try {
    const res = await api.get('core/roles/')
    const data = res.data
    roles.value = Array.isArray(data) ? data : (data?.results ?? [])
  } catch (err) {
    console.error('Roles Error:', err)
  }
}

const fetchLocations = async () => {
  try {
    const res = await api.get('locations-admin/')
    const data = res.data
    const list = Array.isArray(data) ? data : (data?.results ?? [])
    saleLocations.value = list.filter((l) => l.is_sale_location)
  } catch (err) {
    console.error('Locations Error:', err)
  }
}

const fetchUsers = async () => {
  try {
    const res = await api.get('core/employees/')
    const data = res.data
    users.value = Array.isArray(data) ? data : (data?.results ?? [])
  } catch (err) {
    console.error('Users Error:', err)
  }
}

// ၃။ Table မှာ Role Name ပေါ်အောင် လုပ်ဆောင်ပေးမည့် Logic
const getRoleDisplayName = (user) => {
  // ၁။ API က role_name ကို တိုက်ရိုက်ပေးထားရင် အဲဒါက အရှင်းဆုံးပဲ
  if (user.role_name) {
    return user.role_name
  }

  // ၂။ roles list ထဲမှာ ရှာဖို့အတွက် ID ကို နည်းလမ်းမျိုးစုံနဲ့ ရှာမယ်
  // Log အရ role_obj ထဲမှာ ID (integer) တန်းပါနေတာကို တွေ့ရတယ် (ဥပမာ: role_obj: 5)
  let rId = null

  if (typeof user.role_obj === 'number' || typeof user.role_obj === 'string') {
    rId = user.role_obj
  } else if (user.role_obj && typeof user.role_obj === 'object') {
    rId = user.role_obj.id
  } else if (user.role) {
    rId = user.role
  }

  if (!rId) return 'No Role'

  // ၃။ Roles list ထဲမှာ ID နဲ့ တိုက်စစ်မယ်
  if (!roles.value || roles.value.length === 0) return 'Loading...'

  const found = roles.value.find((r) => Number(r.id) === Number(rId))
  return found ? found.name : `ID: ${rId}`
}

// ၄။ Edit Modal ဖွင့်ခြင်း
const openEditModal = (u) => {
  isEdit.value = true
  currentUserId.value = u.id

  // role_obj က integer (5) လည်း ဖြစ်နိုင်သလို object {id: 5} လည်း ဖြစ်နိုင်လို့ နှစ်ခုလုံးစစ်မယ်
  const rId =
    typeof u.role_obj === 'number' || typeof u.role_obj === 'string'
      ? u.role_obj
      : u.role_obj?.id || u.role

  form.value = {
    username: u.username,
    phone_number: u.phone_number || '',
    email: u.email || '',
    role: rId,
    assignment_type: u.assignment_type || 'fixed',
    primary_location: u.primary_location || null,
    assigned_locations: Array.isArray(u.assigned_locations) ? [...u.assigned_locations] : (u.assigned_locations_list ? u.assigned_locations_list.map((l) => l.id) : []),
  }
  activeTab.value = 0
  showModal.value = true
}

const openAddModal = () => {
  isEdit.value = false
  form.value = { username: '', phone_number: '', email: '', password: '', role: '', assignment_type: 'fixed', primary_location: null, assigned_locations: [] }
  activeTab.value = 0
  showModal.value = true
}

// ၅။ Create / Update — backend expects: username, phone_number, email, role_obj, assignment_type, primary_location, assigned_locations, password (create only). ဖုန်း/Email ထည့်ထားရင် ထိုနံပါတ်/အီးမေးလ်နဲ့ ဝင်ရောက်နိုင်မည် (register လို)
const saveUser = async () => {
  submitting.value = true
  try {
    const roleId = form.value.role ? Number(form.value.role) : null
    if (!roleId && !isEdit.value) {
      alert('Role ရွေးချယ်ပါ။')
      submitting.value = false
      return
    }
    const payload = {
      username: String((form.value.username || '').trim()),
      role_obj: roleId,
      assignment_type: form.value.assignment_type || 'fixed',
      primary_location: form.value.primary_location || null,
      assigned_locations: Array.isArray(form.value.assigned_locations) ? form.value.assigned_locations : [],
    }
    const phone = (form.value.phone_number || '').trim()
    const email = (form.value.email || '').trim().toLowerCase()
    payload.phone_number = phone || null
    payload.email = email || ''
    if (!isEdit.value) {
      payload.password = form.value.password || ''
    }

    if (isEdit.value) {
      await api.patch(`core/employees/${currentUserId.value}/`, payload)
    } else {
      await api.post('core/employees/', payload)
    }

    showModal.value = false
    await fetchUsers()
    alert('အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ။')
  } catch (error) {
    const data = error.response?.data
    const msg = typeof data === 'string'
      ? data
      : data?.username?.[0] || data?.phone_number?.[0] || data?.email?.[0] || data?.primary_outlet?.[0] || data?.detail || data?.error || (data && JSON.stringify(data)) || error.message
    console.error('Error Response:', error.response?.data)
    alert('သိမ်းဆည်း၍မရပါ။ ' + (msg || 'Backend key နာမည် မှားယွင်းနေနိုင်ပါသည်။'))
  } finally {
    submitting.value = false
  }
}

// ၆။ Delete
const deleteUser = async (id) => {
  if (!confirm('Are you sure?')) return
  try {
    // api service က auto token injection လုပ်ပေးတယ်
    await api.delete(`core/employees/${id}/`)
    await fetchUsers()
  } catch (err) {
    alert('Delete failed.')
  }
}

// ၇။ အစဉ်လိုက် အလုပ်လုပ်ခြင်း
onMounted(async () => {
  loading.value = true
  await Promise.all([fetchRoles(), fetchLocations()])
  await fetchUsers()
  loading.value = false
})
</script>
