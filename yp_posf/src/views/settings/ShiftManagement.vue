<template>
  <div class="w-full max-w-4xl mx-auto px-4 py-6 space-y-6">
    <h1 class="text-2xl font-bold text-[var(--color-fg)]">{{ t('shift') }} (အလုပ်ချိန်)</h1>
    <p class="text-sm text-[var(--color-fg-muted)]">{{ locale === 'en' ? 'Manage morning/night and other work shifts.' : 'နံနက်/ည စသည့် အလုပ်ချိန်များ စီမံခန့်ခွဲပါ။' }}</p>

    <div class="bg-white rounded-xl border border-[var(--color-border)] shadow-sm overflow-hidden">
      <div class="p-4 border-b border-[var(--color-border)] flex justify-between items-center">
        <h2 class="font-semibold text-[var(--color-fg)]">{{ t('shift_list') }}</h2>
        <button type="button" class="btn-primary px-4 py-2 text-sm" @click="openForm()">+ {{ t('add_shift') }}</button>
      </div>
      <div v-if="loading" class="p-8 text-center text-[var(--color-fg-muted)]">{{ t('loading') }}</div>
      <table v-else class="w-full">
        <thead class="bg-[var(--color-bg-light)]">
          <tr>
            <th class="text-left p-3 text-sm font-semibold text-[var(--color-fg)]">{{ t('name') }}</th>
            <th class="text-left p-3 text-sm font-semibold text-[var(--color-fg)]">Start</th>
            <th class="text-left p-3 text-sm font-semibold text-[var(--color-fg)]">End</th>
            <th class="text-left p-3 text-sm font-semibold text-[var(--color-fg)]">{{ t('active') }}</th>
            <th class="text-right p-3 text-sm font-semibold text-[var(--color-fg)]">{{ t('actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="shifts.length === 0"><td colspan="5" class="p-8 text-center text-[var(--color-fg-muted)]">{{ t('no_shifts_yet') }}</td></tr>
          <tr v-for="s in shifts" :key="s.id" class="border-t border-[var(--color-border)] hover:bg-[var(--color-bg-light)]">
            <td class="p-3 text-[var(--color-fg)] font-medium">{{ s.name }}</td>
            <td class="p-3 text-[var(--color-fg-muted)]">{{ formatTime(s.start_time) }}</td>
            <td class="p-3 text-[var(--color-fg-muted)]">{{ formatTime(s.end_time) }}</td>
            <td class="p-3">
              <span :class="s.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-gray-100 text-gray-600'" class="px-2 py-1 rounded text-xs font-medium">{{ s.is_active ? t('yes') : t('no') }}</span>
            </td>
            <td class="p-3 text-right">
              <button type="button" class="text-[var(--color-primary)] hover:underline text-sm mr-2" @click="openForm(s)">{{ t('edit') }}</button>
              <button type="button" class="text-rose-600 hover:underline text-sm" @click="confirmDelete(s)">{{ t('delete') }}</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Form modal -->
    <div v-if="showForm" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" @click.self="showForm = false">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <h3 class="text-lg font-semibold text-[var(--color-fg)] mb-4">{{ editingId ? t('edit_shift') : t('add_shift') }}</h3>
        <form @submit.prevent="saveShift" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-[var(--color-fg)] mb-1">{{ t('name') }}</label>
            <input v-model="form.name" type="text" required class="w-full min-h-[44px] px-3 rounded-lg border border-[var(--color-border)] text-[var(--color-fg)]" :placeholder="locale === 'en' ? 'e.g. Morning' : 'ဥပမာ နံနက်'" />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-[var(--color-fg)] mb-1">{{ t('start_time') }}</label>
              <input v-model="form.start_time" type="time" required class="w-full min-h-[44px] px-3 rounded-lg border border-[var(--color-border)]" />
            </div>
            <div>
              <label class="block text-sm font-medium text-[var(--color-fg)] mb-1">{{ t('end_time') }}</label>
              <input v-model="form.end_time" type="time" required class="w-full min-h-[44px] px-3 rounded-lg border border-[var(--color-border)]" />
            </div>
          </div>
          <div class="flex items-center gap-2">
            <input v-model="form.is_active" type="checkbox" id="shift-active" class="w-4 h-4 rounded border-[var(--color-border)]" />
            <label for="shift-active" class="text-sm text-[var(--color-fg)]">{{ t('active') }}</label>
          </div>
          <div class="flex gap-2 pt-2">
            <button type="submit" class="btn-primary flex-1 py-2">{{ t('save') }}</button>
            <button type="button" class="btn-secondary flex-1 py-2" @click="showForm = false">{{ t('cancel') }}</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from '@/composables/useI18n'
import api from '@/services/api'

const { t, locale } = useI18n()

const shifts = ref([])
const loading = ref(true)
const showForm = ref(false)
const editingId = ref(null)
const form = reactive({ name: '', start_time: '09:00', end_time: '17:00', is_active: true })

function formatTime(t) {
  if (!t) return '—'
  if (typeof t === 'string' && t.length >= 5) return t.slice(0, 5)
  return t
}

async function fetchShifts() {
  loading.value = true
  try {
    const res = await api.get('core/shifts/')
    shifts.value = Array.isArray(res.data) ? res.data : (res.data?.results ?? [])
  } catch {
    shifts.value = []
  } finally {
    loading.value = false
  }
}

function openForm(shift = null) {
  if (shift) {
    editingId.value = shift.id
    form.name = shift.name
    form.start_time = formatTime(shift.start_time)
    form.end_time = formatTime(shift.end_time)
    form.is_active = shift.is_active !== false
  } else {
    editingId.value = null
    form.name = ''
    form.start_time = '09:00'
    form.end_time = '17:00'
    form.is_active = true
  }
  showForm.value = true
}

async function saveShift() {
  try {
    const payload = { name: form.name, start_time: form.start_time, end_time: form.end_time, is_active: form.is_active }
    if (editingId.value) {
      await api.put(`core/shifts/${editingId.value}/`, payload)
    } else {
      await api.post('core/shifts/', payload)
    }
    showForm.value = false
    fetchShifts()
  } catch (e) {
    alert(e.response?.data?.detail || e.message || 'Save failed')
  }
}

function confirmDelete(s) {
  if (!confirm(`Delete shift "${s.name}"?`)) return
  api.delete(`core/shifts/${s.id}/`).then(() => fetchShifts()).catch((e) => alert(e.response?.data?.detail || 'Delete failed'))
}

onMounted(fetchShifts)
</script>
