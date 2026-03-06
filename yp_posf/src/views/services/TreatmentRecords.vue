<template>
  <div class="p-4 md:p-6 max-w-[1600px] mx-auto space-y-6">
    <div class="flex flex-wrap justify-between items-center gap-4">
      <h1 class="text-2xl font-bold text-[var(--color-fg)]">ကုသမှုမှတ်တမ်း (Treatment Records)</h1>
      <button
        type="button"
        class="px-4 py-2.5 rounded-xl bg-emerald-500 text-white font-bold hover:bg-emerald-600 transition flex items-center gap-2"
        @click="openForm()"
      >
        လူနာအသစ် ထည့်ရန်
      </button>
    </div>

    <div class="bg-white rounded-xl border border-[var(--color-border)] shadow-sm overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-[var(--color-bg-card)] border-b border-[var(--color-border)]">
            <tr>
              <th class="p-4 text-left text-xs font-bold text-[var(--color-fg-muted)] uppercase">လူနာအမည်</th>
              <th class="p-4 text-left text-xs font-bold text-[var(--color-fg-muted)] uppercase">အသက်</th>
              <th class="p-4 text-left text-xs font-bold text-[var(--color-fg-muted)] uppercase">အခြေအနေ</th>
              <th class="p-4 text-left text-xs font-bold text-[var(--color-fg-muted)] uppercase">မတည့်သောဆေး</th>
              <th class="p-4 text-left text-xs font-bold text-[var(--color-fg-muted)] uppercase">ရက်စွဲ</th>
              <th class="p-4 text-center text-xs font-bold text-[var(--color-fg-muted)] uppercase">လုပ်ဆောင်ချက်</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[var(--color-border)]">
            <tr v-if="loading" class="text-center"><td colspan="6" class="p-8 text-[var(--color-fg-muted)]">Loading...</td></tr>
            <tr v-else-if="records.length === 0" class="text-center"><td colspan="6" class="p-8 text-[var(--color-fg-muted)]">မှတ်တမ်းမရှိပါ။</td></tr>
            <tr
              v-else
              v-for="r in records"
              :key="r.id"
              class="hover:bg-[var(--color-bg-light)]"
            >
              <td class="p-4 font-semibold text-[var(--color-fg)]">{{ r.patient_name }}</td>
              <td class="p-4 text-[var(--color-fg)]">{{ r.age ?? '—' }}</td>
              <td class="p-4 text-[var(--color-fg)] max-w-[200px] truncate">{{ r.condition || '—' }}</td>
              <td class="p-4 text-[var(--color-fg)] max-w-[180px] truncate">{{ r.drug_allergies || '—' }}</td>
              <td class="p-4 text-sm text-[var(--color-fg-muted)]">{{ formatDate(r.created_at) }}</td>
              <td class="p-4 text-center">
                <button type="button" class="text-sky-600 hover:underline mr-2" @click="viewDetail(r)">ကြည့်ရန်</button>
                <button type="button" class="text-emerald-600 hover:underline mr-2" @click="openForm(r)">ပြင်ဆင်ရန်</button>
                <button type="button" class="text-rose-600 hover:underline" @click="confirmDelete(r)">ဖျက်ရန်</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal: Add/Edit -->
    <div v-if="showForm" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-xl max-w-lg w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto">
        <h2 class="text-xl font-bold text-[var(--color-fg)]">{{ editingId ? 'ပြင်ဆင်ရန်' : 'လူနာအသစ် ထည့်ရန်' }}</h2>
        <div>
          <label class="block mb-1 text-sm font-medium text-[var(--color-fg)]">လူနာအမည်</label>
          <input v-model="form.patient_name" class="w-full px-4 py-2 border rounded-lg" required />
        </div>
        <div>
          <label class="block mb-1 text-sm font-medium text-[var(--color-fg)]">အသက်</label>
          <input v-model.number="form.age" type="number" min="0" class="w-full px-4 py-2 border rounded-lg" />
        </div>
        <div>
          <label class="block mb-1 text-sm font-medium text-[var(--color-fg)]">အခြေအနေ / ရောဂါဖော်ပြချက်</label>
          <textarea v-model="form.condition" rows="3" class="w-full px-4 py-2 border rounded-lg"></textarea>
        </div>
        <div>
          <label class="block mb-1 text-sm font-medium text-[var(--color-fg)]">မတည့်သောဆေးများ</label>
          <textarea v-model="form.drug_allergies" rows="2" class="w-full px-4 py-2 border rounded-lg" placeholder="Comma or line separated"></textarea>
        </div>
        <div>
          <label class="block mb-1 text-sm font-medium text-[var(--color-fg)]">မှတ်ချက်</label>
          <textarea v-model="form.notes" rows="2" class="w-full px-4 py-2 border rounded-lg"></textarea>
        </div>
        <div class="flex gap-3 pt-2">
          <button type="button" class="flex-1 py-2.5 border rounded-xl font-bold" @click="showForm = false">ပယ်ဖျက်</button>
          <button type="button" class="flex-1 py-2.5 bg-emerald-500 text-white rounded-xl font-bold" @click="saveRecord">သိမ်းမည်</button>
        </div>
      </div>
    </div>

    <!-- Modal: Detail + Files (X-ray, Ultrasound) -->
    <div v-if="selectedRecord" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div class="bg-white rounded-xl max-w-2xl w-full p-6 space-y-4 my-8 max-h-[90vh] overflow-y-auto">
        <h2 class="text-xl font-bold text-[var(--color-fg)]">ကုသမှုမှတ်တမ်း ကြည့်ရန်</h2>
        <div class="grid grid-cols-2 gap-2 text-sm">
          <div><span class="text-[var(--color-fg-muted)]">လူနာအမည်</span><br><span class="font-semibold">{{ selectedRecord.patient_name }}</span></div>
          <div><span class="text-[var(--color-fg-muted)]">အသက်</span><br><span class="font-semibold">{{ selectedRecord.age ?? '—' }}</span></div>
          <div class="col-span-2"><span class="text-[var(--color-fg-muted)]">အခြေအနေ</span><br><span class="font-semibold whitespace-pre-wrap">{{ selectedRecord.condition || '—' }}</span></div>
          <div class="col-span-2"><span class="text-[var(--color-fg-muted)]">မတည့်သောဆေး</span><br><span class="font-semibold whitespace-pre-wrap">{{ selectedRecord.drug_allergies || '—' }}</span></div>
        </div>
        <div>
          <h3 class="font-bold text-[var(--color-fg)] mb-2">ဓာတ်မှန် / အယ်ထရာဆောင်း ပုံများ</h3>
          <div class="space-y-2">
            <div v-for="f in (selectedRecord.files || [])" :key="f.id" class="flex items-center justify-between p-2 border rounded-lg">
              <span class="text-sm">{{ f.file_type }} – {{ f.caption || '—' }}</span>
              <a v-if="f.file_url" :href="f.file_url" target="_blank" rel="noopener" class="text-sky-600 text-sm">ဖိုင်ဖွင့်ကြည့်ရန်</a>
            </div>
            <p v-if="!selectedRecord.files?.length" class="text-sm text-[var(--color-fg-muted)]">ဖိုင်မရှိပါ။</p>
          </div>
          <div class="mt-3">
            <label class="block mb-1 text-sm font-medium">ဖိုင်တင်ရန် (X-Ray / Ultrasound)</label>
            <input ref="fileInput" type="file" accept="image/*,.pdf" class="text-sm" @change="onFileSelect" />
            <button type="button" class="mt-2 px-3 py-1.5 bg-sky-500 text-white rounded-lg text-sm" @click="uploadFile" :disabled="!pendingFile">တင်မည်</button>
          </div>
        </div>
        <button type="button" class="w-full py-2.5 border rounded-xl font-bold" @click="selectedRecord = null">ပိတ်မည်</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

const records = ref([])
const loading = ref(false)
const showForm = ref(false)
const editingId = ref(null)
const selectedRecord = ref(null)
const fileInput = ref(null)
const pendingFile = ref(null)

const form = ref({
  patient_name: '',
  age: null,
  condition: '',
  drug_allergies: '',
  notes: '',
})

function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-CA')
}

async function fetchRecords() {
  loading.value = true
  try {
    const res = await api.get('service/treatment-records/')
    records.value = res.data.results ?? res.data ?? []
  } catch (e) {
    console.error(e)
    records.value = []
  } finally {
    loading.value = false
  }
}

function openForm(record = null) {
  editingId.value = record?.id ?? null
  form.value = {
    patient_name: record?.patient_name ?? '',
    age: record?.age ?? null,
    condition: record?.condition ?? '',
    drug_allergies: record?.drug_allergies ?? '',
    notes: record?.notes ?? '',
  }
  showForm.value = true
}

async function saveRecord() {
  if (!form.value.patient_name.trim()) return
  try {
    if (editingId.value) {
      await api.patch(`service/treatment-records/${editingId.value}/`, form.value)
    } else {
      await api.post('service/treatment-records/', form.value)
    }
    await fetchRecords()
    showForm.value = false
  } catch (e) {
    console.error(e)
    alert('သိမ်းခြင်း မအောင်မြင်ပါ။')
  }
}

async function viewDetail(record) {
  try {
    const res = await api.get(`service/treatment-records/${record.id}/`)
    selectedRecord.value = res.data
    pendingFile.value = null
    if (fileInput.value) fileInput.value.value = ''
  } catch (e) {
    console.error(e)
  }
}

function onFileSelect(e) {
  pendingFile.value = e.target?.files?.[0] ?? null
}

async function uploadFile() {
  if (!pendingFile.value || !selectedRecord.value) return
  const fd = new FormData()
  fd.append('file', pendingFile.value)
  fd.append('file_type', 'other')
  try {
    await api.post(`service/treatment-records/${selectedRecord.value.id}/upload-file/`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    const res = await api.get(`service/treatment-records/${selectedRecord.value.id}/`)
    selectedRecord.value = res.data
    pendingFile.value = null
    if (fileInput.value) fileInput.value.value = ''
  } catch (e) {
    console.error(e)
    alert('ဖိုင်တင်ခြင်း မအောင်မြင်ပါ။')
  }
}

async function confirmDelete(record) {
  if (!confirm(`"${record.patient_name}" မှတ်တမ်းကို ဖျက်မှာ သေချာပါသလား?`)) return
  try {
    await api.delete(`service/treatment-records/${record.id}/`)
    await fetchRecords()
    if (selectedRecord.value?.id === record.id) selectedRecord.value = null
  } catch (e) {
    console.error(e)
    alert('ဖျက်ခြင်း မအောင်မြင်ပါ။')
  }
}

onMounted(() => {
  fetchRecords()
})
</script>
