<template>
  <div class="glass-card p-4 md:p-6 rounded-2xl space-y-6 border border-[var(--surface-border)]">
    <h2 class="text-lg font-bold text-white/90 border-b border-[var(--surface-border)] pb-4">စက်ပြင်လက်ခံလွှာ</h2>

    <div class="space-y-2">
      <label class="glass-label text-sm font-bold text-white/80 flex justify-between items-center">
        ဝယ်ယူသူ ရွေးချယ်ပါ
        <button
          @click="showNewCustomerModal = true"
          type="button"
          class="text-xs text-amber-400 font-bold hover:text-amber-300 flex items-center gap-1 transition-colors"
        >
          <PlusCircle class="w-4 h-4" /> ဝယ်ယူသူအသစ်ထည့်ရန်
        </button>
      </label>
      <select
        v-model="form.customer"
        class="glass-input w-full p-3 rounded-xl text-white/90 outline-none focus:ring-1 focus:ring-white/30"
        required
      >
        <option value="" disabled>ဝယ်ယူသူကို ရွေးချယ်ပါ</option>
        <option v-for="c in customers" :key="c.id" :value="c.id">
          {{ c.name }} ({{ c.phone_number }})
        </option>
      </select>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div class="space-y-1">
        <label class="glass-label text-xs font-bold text-white/60 uppercase">ပစ္စည်းအမည်</label>
        <input
          v-model="form.item_name"
          type="text"
          class="glass-input w-full p-3 rounded-xl text-white/90 placeholder-white/40 outline-none focus:ring-1 focus:ring-white/30"
          placeholder="ဥပမာ- စက်ပစ္စည်း"
        />
      </div>
      <div class="space-y-1">
        <label class="glass-label text-xs font-bold text-white/60 uppercase">ပြန်ပေးရမည့်ရက်</label>
        <input
          v-model="form.return_date"
          type="date"
          class="glass-input w-full p-3 rounded-xl text-white/90 outline-none focus:ring-1 focus:ring-white/30"
        />
      </div>
    </div>

    <div class="space-y-1">
      <label class="glass-label text-xs font-bold text-white/60 uppercase">ဖြစ်ပွားသည့် ပြဿနာ</label>
      <textarea
        v-model="form.problem_description"
        class="glass-input w-full p-3 rounded-xl text-white/90 placeholder-white/40 outline-none focus:ring-1 focus:ring-white/30 resize-none"
        rows="2"
        placeholder="အသေးစိတ် ရေးပေးပါ"
      ></textarea>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div class="space-y-1">
        <label class="glass-label text-xs font-bold text-white/60 uppercase">ခန့်မှန်းကုန်ကျစရိတ်</label>
        <input
          v-model.number="form.total_estimated_cost"
          type="number"
          class="glass-input w-full p-3 rounded-xl font-mono text-white/90 outline-none focus:ring-1 focus:ring-white/30"
        />
      </div>
      <div class="space-y-1">
        <label class="glass-label text-xs font-bold text-white/60 uppercase">စရန်ငွေ</label>
        <input
          v-model.number="form.deposit_amount"
          type="number"
          class="glass-input w-full p-3 rounded-xl font-mono text-white/90 outline-none focus:ring-1 focus:ring-white/30"
        />
      </div>
    </div>

    <button
      @click="submitService"
      class="w-full py-4 rounded-2xl font-bold transition-all bg-white/15 hover:bg-white/25 text-white border border-[var(--surface-border)]"
    >
      စက်ပြင်လက်ခံလွှာ သိမ်းဆည်းမည်
    </button>

    <div
      v-if="showNewCustomerModal"
      class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[70] p-4"
      @click.self="showNewCustomerModal = false"
    >
      <div class="glass-card rounded-2xl p-6 w-full max-w-md border border-[var(--surface-border)]">
        <h3 class="text-lg font-bold mb-4 flex items-center gap-2 text-white/90">
          <UserPlus class="w-5 h-5 text-amber-400" /> ဝယ်ယူသူအသစ် မှတ်ပုံတင်ခြင်း
        </h3>
        <div class="space-y-4">
          <input
            v-model="newCustomer.name"
            type="text"
            class="glass-input w-full p-3 rounded-xl text-white/90 placeholder-white/40 outline-none focus:ring-1 focus:ring-white/30"
            placeholder="အမည်"
          />
          <input
            v-model="newCustomer.phone_number"
            type="text"
            class="glass-input w-full p-3 rounded-xl text-white/90 placeholder-white/40 outline-none focus:ring-1 focus:ring-white/30"
            placeholder="ဖုန်းနံပါတ်"
          />
          <textarea
            v-model="newCustomer.address"
            class="glass-input w-full p-3 rounded-xl text-white/90 placeholder-white/40 outline-none focus:ring-1 focus:ring-white/30 resize-none"
            placeholder="လိပ်စာ"
          ></textarea>
        </div>
        <div class="flex justify-end gap-3 mt-6">
          <button
            @click="showNewCustomerModal = false"
            class="px-4 py-2 rounded-xl glass-surface text-white/70 hover:text-white/90 border border-[var(--surface-border)]"
          >
            Cancel
          </button>
          <button
            @click="createNewCustomer"
            class="px-6 py-2 rounded-xl font-bold bg-amber-500 text-white hover:bg-amber-600 border border-amber-400/30 transition-colors"
          >
            သိမ်းမည်
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { PlusCircle, UserPlus } from 'lucide-vue-next'
import api from '@/services/api'

const emit = defineEmits(['saved'])

// ၁။ Form State
const form = ref({
  customer: '',
  item_name: '',
  problem_description: '',
  total_estimated_cost: 0,
  deposit_amount: 0,
  return_date: '',
  status: 'received',
})

const showNewCustomerModal = ref(false)
const customers = ref([])
const newCustomer = ref({ name: '', phone_number: '', address: '' })

// api service က auto token injection လုပ်ပေးတယ်

// ၃။ Customer List ခေါ်ယူခြင်း
const fetchCustomers = async () => {
  try {
    const res = await api.get('customers/')
    customers.value = res.data.results || res.data
  } catch (err) {
    console.error('Fetch error:', err.response)
  }
}

// ၄။ Customer အသစ် Create လုပ်ခြင်း (Variable အမည်များ မှန်အောင် ပြင်ထားသည်)
const createNewCustomer = async () => {
  if (!newCustomer.value.name || !newCustomer.value.phone_number) {
    alert('အမည်နှင့် ဖုန်းနံပါတ် ဖြည့်ပေးပါ')
    return
  }
  try {
    const res = await api.post('customers/', newCustomer.value)

    // List ထဲပေါင်းထည့်ပြီး တစ်ခါတည်း ရွေးချယ်ပေးလိုက်ခြင်း
    customers.value.push(res.data)
    form.value.customer = res.data.id // form.customer ကို သုံးရပါမည်

    // Modal ပိတ်ပြီး Data ရှင်းခြင်း
    showNewCustomerModal.value = false
    newCustomer.value = { name: '', phone_number: '', address: '' }
    alert('ဝယ်ယူသူအသစ် သိမ်းဆည်းပြီးပါပြီ')
  } catch (e) {
    console.error(e)
    alert(e.response?.data?.detail || 'Error creating customer')
  }
}

// ၅။ စက်ပြင်လက်ခံလွှာ တစ်ခုလုံး သိမ်းဆည်းခြင်း
const submitService = async () => {
  if (!form.value.customer || !form.value.item_name || !form.value.return_date) {
    alert('ကျေးဇူးပြု၍ အချက်အလက်များ ပြည့်စုံအောင် ဖြည့်ပေးပါ')
    return
  }
  try {
    const res = await api.post('service/repairs/', form.value)
    alert('စက်ပြင်လက်ခံလွှာ သိမ်းဆည်းပြီးပါပြီ')
    emit('saved', res.data)

    // Form Reset
    form.value = {
      customer: '',
      item_name: '',
      problem_description: '',
      total_estimated_cost: 0,
      deposit_amount: 0,
      return_date: '',
      status: 'received',
    }
  } catch (error) {
    console.error(error)
    alert(error.response?.data?.detail || 'စက်ပြင်လွှာ သိမ်းလို့မရပါ။')
  }
}

onMounted(fetchCustomers)
defineExpose({ form, fetchCustomers })
</script>
