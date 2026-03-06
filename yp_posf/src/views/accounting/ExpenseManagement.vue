<template>
  <div class="flex-1 p-4 md:p-6 space-y-6 max-w-[1600px] mx-auto bg-[#f4f4f4] min-h-full">
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-black tracking-tight text-[#1a1a1a]">{{ t('expense_management') }}</h1>
        <p class="text-xs font-bold text-[#6b7280] uppercase tracking-wider mt-1">{{ locale === 'en' ? 'Expense Management' : 'ကုန်ကျစရိတ် စီမံခန့်ခွဲမှု' }}</p>
      </div>
      <button
        @click="showAddModal = true"
        class="px-4 py-2.5 rounded-xl bg-emerald-500 text-white font-bold text-sm hover:bg-emerald-600 transition-all flex items-center gap-2"
      >
        <Plus class="w-4 h-4" />
        {{ t('add_expense') }}
      </button>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-xl border border-[var(--color-border)] shadow-sm p-4 flex flex-wrap gap-4">
      <div class="flex-1 min-w-[200px]">
        <label class="block mb-2 text-sm font-medium text-[#374151]">{{ t('start_date') }}</label>
        <input
          v-model="filters.startDate"
          type="date"
          class="glass-input w-full px-4 py-2"
          @change="fetchExpenses"
        />
      </div>
      <div class="flex-1 min-w-[200px]">
        <label class="block mb-2 text-sm font-medium text-[#374151]">{{ t('end_date') }}</label>
        <input
          v-model="filters.endDate"
          type="date"
          class="glass-input w-full px-4 py-2"
          @change="fetchExpenses"
        />
      </div>
      <div class="flex items-end">
        <button
          @click="fetchExpenses"
          class="px-4 py-2 rounded-xl border border-[var(--color-border)] bg-white text-[#1a1a1a] font-bold text-sm hover:bg-[#f3f4f6] transition-all"
        >
          <RefreshCw :class="{ 'animate-spin': loading }" class="w-4 h-4 inline-block mr-2" />
          {{ t('refresh') }}
        </button>
      </div>
    </div>

    <!-- Expenses Table -->
    <div class="bg-white rounded-xl border border-[var(--color-border)] shadow-sm overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-[var(--color-bg-card)] border-b border-[var(--color-border)]">
            <tr>
              <th class="p-4 text-left text-xs font-bold text-[#6b7280] uppercase">{{ t('date') }}</th>
              <th class="p-4 text-left text-xs font-bold text-[#6b7280] uppercase">{{ t('category') }}</th>
              <th class="p-4 text-left text-xs font-bold text-[#6b7280] uppercase">{{ t('description') }}</th>
              <th class="p-4 text-right text-xs font-bold text-[#6b7280] uppercase">{{ t('amount') }}</th>
              <th class="p-4 text-left text-xs font-bold text-[#6b7280] uppercase">{{ t('recorded_by') }}</th>
              <th class="p-4 text-center text-xs font-bold text-[#6b7280] uppercase">{{ t('action') }}</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[var(--color-border)]">
            <tr v-if="loading" class="text-center">
              <td colspan="6" class="p-8 text-[#6b7280]">{{ locale === 'en' ? 'Loading...' : 'ဆောင်းချက်နေသည်...' }}</td>
            </tr>
            <tr v-else-if="apiError" class="text-center">
              <td colspan="6" class="p-8 text-rose-600">{{ apiError }}</td>
            </tr>
            <tr v-else-if="expenses.length === 0" class="text-center">
              <td colspan="6" class="p-8 text-[#6b7280]">{{ t('no_expenses_yet') }}</td>
            </tr>
            <tr v-else v-for="expense in expenses" :key="expense.id" class="hover:bg-[var(--color-bg-card)]">
              <td class="p-4 text-[#1a1a1a] text-sm">{{ formatDate(expense.expense_date) }}</td>
              <td class="p-4">
                <span class="bg-[var(--color-bg-card)] text-[#374151] border border-[var(--color-border)] px-2 py-1 rounded text-xs font-bold">
                  {{ expense.category_name }}
                </span>
              </td>
              <td class="p-4 text-[#1a1a1a] text-sm">{{ expense.description }}</td>
              <td class="p-4 text-right text-[#1a1a1a] font-bold">{{ formatCurrency(expense.amount) }}</td>
              <td class="p-4 text-[#4b5563] text-sm">{{ expense.created_by_username || '-' }}</td>
              <td class="p-4 text-center">
                <button
                  @click="editExpense(expense)"
                  class="text-sky-600 hover:text-sky-700 mr-2"
                >
                  <Edit class="w-4 h-4 inline" />
                </button>
                <button
                  @click="deleteExpense(expense.id)"
                  class="text-rose-600 hover:text-rose-700"
                >
                  <Trash2 class="w-4 h-4 inline" />
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Add/Edit Modal -->
    <div v-if="showAddModal || editingExpense" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white max-w-md w-full p-6 space-y-4 rounded-xl border border-[var(--color-border)] shadow-xl">
        <h2 class="text-xl font-bold text-[#1a1a1a]">
          {{ editingExpense ? t('edit_expense') : t('add_expense') }}
        </h2>
        
        <div>
          <label class="block mb-2 text-sm font-medium text-[#374151]">{{ t('category') }}</label>
          <select v-model="form.category" class="glass-input w-full px-4 py-2" required>
            <option value="">{{ t('select_category') }}</option>
            <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
          </select>
        </div>

        <div>
          <label class="block mb-2 text-sm font-medium text-[#374151]">{{ t('description') }}</label>
          <input
            v-model="form.description"
            type="text"
            class="glass-input w-full px-4 py-2"
            placeholder="ဥပမာ: ဇန်နဝါရီလ အငှားချ"
            required
          />
        </div>

        <div>
          <label class="block mb-2 text-sm font-medium text-[#374151]">{{ t('amount') }} (MMK)</label>
          <input
            v-model.number="form.amount"
            type="number"
            min="0"
            step="1"
            class="glass-input w-full px-4 py-2"
            placeholder="500000"
            required
          />
        </div>

        <div>
          <label class="block mb-2 text-sm font-medium text-[#374151]">{{ t('date') }}</label>
          <input
            v-model="form.expense_date"
            type="date"
            class="glass-input w-full px-4 py-2"
            required
          />
        </div>

        <div>
          <label class="block mb-2 text-sm font-medium text-[#374151]">{{ t('notes') }}</label>
          <textarea
            v-model="form.notes"
            class="glass-input w-full px-4 py-2"
            rows="3"
            placeholder="ထပ်မံ ဖော်ပြလိုသော အချက်အလက်"
          />
        </div>

        <div class="flex gap-3 pt-4">
          <button
            @click="saveExpense"
            :disabled="saving"
            class="flex-1 px-4 py-2 rounded-xl bg-emerald-500 text-white font-bold hover:bg-emerald-600 transition-all disabled:opacity-70"
          >
            {{ saving ? (locale === 'en' ? 'Saving...' : 'သိမ်းဆည်းနေသည်...') : t('save') }}
          </button>
          <button
            @click="cancelEdit"
            class="flex-1 px-4 py-2 rounded-xl border border-[var(--color-border)] bg-white text-[#1a1a1a] font-bold hover:bg-[#f3f4f6] transition-all"
          >
            {{ t('cancel') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Plus, RefreshCw, Edit, Trash2 } from 'lucide-vue-next'
import { useI18n } from '@/composables/useI18n'
import api from '@/services/api'

const { t, locale } = useI18n()

const expenses = ref([])
const categories = ref([])
const loading = ref(false)
const saving = ref(false)
const apiError = ref('')
const showAddModal = ref(false)
const editingExpense = ref(null)

function getDefaultDateRange() {
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - 90)
  return {
    startDate: start.toISOString().split('T')[0],
    endDate: end.toISOString().split('T')[0],
  }
}
const filters = ref(getDefaultDateRange())

const form = ref({
  category: '',
  description: '',
  amount: '',
  expense_date: new Date().toISOString().split('T')[0],
  notes: '',
})

const fetchCategories = async () => {
  try {
    const res = await api.get('accounting/expense-categories/')
    categories.value = res.data?.results ?? res.data ?? []
  } catch (e) {
    console.error(e)
    categories.value = []
  }
}

const fetchExpenses = async () => {
  loading.value = true
  apiError.value = ''
  try {
    const params = {}
    if (filters.value.startDate) params.start_date = filters.value.startDate
    if (filters.value.endDate) params.end_date = filters.value.endDate
    const res = await api.get('accounting/expenses/', { params })
    expenses.value = res.data?.results ?? res.data ?? []
  } catch (e) {
    console.error(e)
    expenses.value = []
    const msg = e.response?.data?.detail || e.message || (locale.value === 'en' ? 'Failed to load expenses.' : 'ကုန်ကျစရိတ် မရနိုင်ပါ။')
    apiError.value = typeof msg === 'string' ? msg : (locale.value === 'en' ? 'Failed to load expenses.' : 'ကုန်ကျစရိတ် မရနိုင်ပါ။')
  } finally {
    loading.value = false
  }
}

const saveExpense = async () => {
  if (!form.value.category || !form.value.description || !form.value.amount) {
    alert('ကျေးဇူးပြု၍ အချက်အလက်အားလုံး ဖြည့်သွင်းပါ။')
    return
  }

  saving.value = true
  try {
    // api service က auto token injection လုပ်ပေးတယ်
    if (editingExpense.value) {
      await api.put(`accounting/expenses/${editingExpense.value.id}/`, form.value)
    } else {
      await api.post('accounting/expenses/', form.value)
    }
    
    await fetchExpenses()
    cancelEdit()
  } catch (e) {
    console.error(e)
    alert('သိမ်းဆည်းခြင်း မအောင်မြင်ပါ။')
  } finally {
    saving.value = false
  }
}

const editExpense = (expense) => {
  editingExpense.value = expense
  form.value = {
    category: expense.category,
    description: expense.description,
    amount: expense.amount,
    expense_date: expense.expense_date,
    notes: expense.notes || '',
  }
}

const deleteExpense = async (id) => {
  if (!confirm('ဤကုန်ကျစရိတ်ကို ဖျက်ရန် သေချာပါသလား?')) return
  
  try {
    // api service က auto token injection လုပ်ပေးတယ်
    await api.delete(`accounting/expenses/${id}/`)
    await fetchExpenses()
  } catch (e) {
    console.error(e)
    alert('ဖျက်ခြင်း မအောင်မြင်ပါ။')
  }
}

const cancelEdit = () => {
  showAddModal.value = false
  editingExpense.value = null
  form.value = {
    category: '',
    description: '',
    amount: '',
    expense_date: new Date().toISOString().split('T')[0],
    notes: '',
  }
}

const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('my-MM', { year: 'numeric', month: 'short', day: 'numeric' })
}

const formatCurrency = (amount) => {
  if (!amount) return '0 MMK'
  return Math.round(Number(amount) || 0).toLocaleString('my-MM', { maximumFractionDigits: 0, minimumFractionDigits: 0 }) + ' MMK'
}

onMounted(() => {
  fetchCategories()
  fetchExpenses()
})
</script>
