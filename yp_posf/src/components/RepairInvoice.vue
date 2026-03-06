<!-- <template>
  <div v-if="repair" class="invoice-wrapper print:m-0 print:p-0">
    <div
      class="bg-white mx-auto relative shadow-lg print:shadow-none print:static print:w-full"
      style="width: 210mm; min-height: 297mm; padding: 30mm; font-family: sans-serif"
      id="printable-invoice"
    >
      <div
        v-if="repair.status === 'delivered'"
        class="absolute top-1/3 left-1/2 -translate-x-1/2 border-[12px] border-green-500/10 text-green-500/10 font-black text-9xl p-10 rounded-[50px] -rotate-12 select-none z-0"
      >
        PAID
      </div>

      <div
        class="flex justify-between items-start border-b-4 border-gray-900 pb-8 mb-10 relative z-10"
      >
        <div class="flex items-center gap-6">
          <img :src="logoImage" class="w-16 h-16 object-contain" alt="Logo" />
          <div>
            <h1 class="text-3xl font-black uppercase tracking-tighter text-gray-900 leading-none">
              {{ shopName }}
            </h1>
            <p class="text-xs font-bold text-gray-500 uppercase mt-2">
              {{ shopName }}
            </p>
          </div>
        </div>
        <div class="text-right">
          <h2
            class="bg-blue-50 text-blue-700 text-xs font-black uppercase tracking-widest px-4 py-2 rounded-lg border border-blue-100 inline-block mb-4"
          >
            {{ repair.status === 'delivered' ? 'Official Receipt' : 'Deposit Receipt' }}
          </h2>
          <div class="text-sm font-bold text-gray-600 space-y-1">
            <p>
              No: <span class="text-gray-900 font-mono">{{ repair.repair_no }}</span>
            </p>
            <p>Date: {{ new Date().toLocaleDateString() }}</p>
            <p class="text-red-600 uppercase">Staff: Admin</p>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-12 mb-10 relative z-10">
        <div class="bg-gray-50 p-6 rounded-2xl border border-gray-100">
          <p class="text-[10px] font-black text-gray-400 uppercase mb-2">Customer Info</p>
          <p class="text-lg font-black text-gray-900">{{ repair.customer_info?.name }}</p>
          <p class="text-sm text-gray-600">{{ repair.customer_info?.phone_number }}</p>
        </div>
        <div class="text-right p-6">
          <p class="text-[10px] font-black text-gray-400 uppercase mb-2">Estimated Return Date</p>
          <p class="text-2xl font-black text-blue-700 underline decoration-4 underline-offset-8">
            {{ repair.return_date }}
          </p>
        </div>
      </div>

      <div class="rounded-2xl border-2 border-gray-900 overflow-hidden mb-12 relative z-10">
        <table class="w-full text-base">
          <thead class="bg-gray-900 text-white uppercase text-xs tracking-widest font-bold">
            <tr>
              <th class="py-5 px-8 text-left">Service Description</th>
              <th class="py-5 px-8 text-right font-bold">Amount (MMK)</th>
            </tr>
          </thead>
          <tbody class="divide-y-2 divide-gray-900 font-bold italic">
            <tr>
              <td class="p-8">
                <p class="text-2xl font-black text-gray-900 uppercase mb-3">
                  {{ repair.item_name }}
                </p>
                <p class="text-sm text-gray-500 leading-relaxed">
                  {{ repair.problem_description }}
                </p>
              </td>
              <td class="p-8 text-right font-mono text-2xl">
                {{ Math.round(Number(repair.total_estimated_cost) || 0).toLocaleString(undefined, { maximumFractionDigits: 0 }) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="flex justify-between items-start mb-24 relative z-10">
        <div class="print:hidden flex flex-col gap-3 pt-2">
          <button
            v-if="repair.status === 'received'"
            @click="triggerUpdate('ready')"
            class="bg-blue-600 text-white px-8 py-3 rounded-xl text-xs font-black shadow-lg hover:bg-blue-700 transition"
          >
            MARK AS READY
          </button>
          <button
            v-if="repair.status === 'ready'"
            @click="triggerUpdate('delivered')"
            class="bg-green-600 text-white px-8 py-3 rounded-xl text-xs font-black shadow-lg hover:bg-green-700 transition"
          >
            DELIVER & PAID
          </button>
          <button
            @click="handlePrint"
            class="bg-gray-900 text-white px-8 py-3 rounded-xl text-xs font-black shadow-lg hover:bg-black transition"
          >
            🖨️ PRINT INVOICE
          </button>
        </div>

        <div class="w-80 space-y-4">
          <div class="flex justify-between text-sm font-bold text-gray-400 px-2 uppercase">
            <span>Subtotal</span>
            <span class="font-mono text-gray-900">{{
              Math.round(Number(repair.total_estimated_cost) || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })
            }}</span>
          </div>
          <div
            class="flex justify-between text-sm font-bold text-green-600 bg-green-50 p-4 rounded-xl border border-green-100 uppercase"
          >
            <span>Deposit Paid (-)</span>
            <span class="font-mono">- {{ Math.round(Number(repair.deposit_amount) || 0).toLocaleString(undefined, { maximumFractionDigits: 0 }) }}</span>
          </div>
          <div
            class="flex justify-between text-3xl border-t-4 border-gray-900 pt-6 font-black uppercase italic tracking-tighter"
          >
            <span>{{ repair.status === 'delivered' ? 'TOTAL PAID' : 'BALANCE' }}</span>
            <span
              :class="repair.status === 'delivered' ? 'text-green-600' : 'text-red-600'"
              class="font-mono underline"
            >
              {{
                repair.status === 'delivered' ? '0' : Math.round(Number(repair.balance_amount) || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })
              }}
            </span>
          </div>
        </div>
      </div>

      <div class="mt-auto grid grid-cols-2 gap-32 text-center px-10">
        <div
          class="border-t-2 border-gray-300 pt-5 text-xs font-black uppercase text-gray-400 tracking-widest"
        >
          Customer
        </div>
        <div
          class="border-t-2 border-gray-300 pt-5 text-xs font-black uppercase text-gray-400 tracking-widest"
        >
          Authorized Sign
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'
import axios from 'axios'
import { API_URL } from '@/config'
const logoImage = (import.meta.env.BASE_URL || '/') + 'logo.svg'

const props = defineProps({
  repair: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['updated'])

const getAuthConfig = () => ({
  headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
})

// Status Update Function
const triggerUpdate = async (newStatus) => {
  try {
    const res = await axios.patch(
      `${API_URL}service/repairs/${props.repair.id}/`,
      { status: newStatus },
      getAuthConfig(),
    )
    emit('updated', res.data)
  } catch (err) {
    alert('Status update failed!')
    console.error(err)
  }
}

// Print Function (TypeError မဖြစ်အောင် ဒီမှာ ရေးပေးရသည်)
const handlePrint = () => {
  window.print()
}
</script>

<style scoped>
@media print {
  @page {
    size: portrait;
    margin: 0;
  }
  body {
    -webkit-print-color-adjust: exact;
    background: white !important;
  }
  /* Vue DevTools နှင့် အခြား UI element များကို အရှင်းဆုံးဖျောက်ခြင်း */
  [class*='vue-devtools'],
  .v-overlay,
  .print\:hidden,
  [data-v-inspector],
  button {
    display: none !important;
  }
  #printable-invoice {
    position: absolute !important;
    top: 0;
    left: 0;
    width: 210mm;
    height: 297mm;
    margin: 0 !important;
    padding: 15mm !important; /* စာရွက်အနားသတ် */
  }
}
</style> -->

<template>
  <div v-if="repair" id="printable-invoice" class="bg-white mx-auto relative text-left">
    <div
      v-if="repair.status === 'completed'"
      class="absolute top-1/4 left-1/2 -translate-x-1/2 border-[10px] border-red-500/20 text-red-500/20 font-black text-9xl p-10 rounded-[50px] -rotate-12 select-none z-0 uppercase"
    >
      PAID
    </div>

    <div
      class="flex justify-between items-start border-b-4 border-gray-900 pb-8 mb-10 relative z-10 -mt-2"
    >
      <div class="flex items-center gap-6">
        <img :src="logoImage" class="w-16 h-16 object-contain" alt="Logo" />
        <div>
          <h1 class="text-[14px] font-black uppercase tracking-tighter text-gray-900 leading-none">
            {{ shopName }}
          </h1>
          <p class="text-[12px] font-bold text-gray-500 uppercase mt-2">
            {{ shopName }}
          </p>
        </div>
      </div>
      <div class="text-right">
        <h2
          class="text-blue-700 text-[12px] font-black uppercase tracking-widest px-4 py-2 rounded-lg border border-blue-100 inline-block mb-4"
        >
          {{ repair.status === 'completed' ? 'Paided Receipt' : 'Deposit Receipt' }}
        </h2>
        <div class="text-[12px] font-bold text-gray-600 space-y-1 font-mono">
          <p>
            No: <span class="text-gray-900 font-black">{{ repair.repair_no }}</span>
          </p>
          <p>Date: {{ new Date().toLocaleDateString() }}</p>
          <p class="text-red-600 uppercase font-bold">Staff: Admin</p>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-2 gap-12 mb-5 relative z-10 -mt-10">
      <div class="p-4 -mt-2">
        <p class="text-[10px] font-black text-gray-400 uppercase mb-2">Customer Info</p>
        <p class="text-[12px] font-black text-gray-900">{{ repair.customer_info?.name }}</p>
        <p class="text-[12px] text-gray-600 font-bold">{{ repair.customer_info?.phone_number }}</p>
      </div>
      <div class="text-right p-4 -mt-2">
        <p class="text-[10px] font-black text-gray-400 uppercase mb-2">Estimated Return Date</p>
        <p class="text-[16px] font-black text-blue-700 underline decoration-4 underline-offset-8">
          {{ repair.return_date }}
        </p>
      </div>
    </div>

    <div class="border-4 border-gray-900 rounded-[20px] p-5 mb-5 relative z-10 overflow-hidden">
      <div class="flex justify-between items-start mb-3">
        <span class="text-[10px] font-black text-gray-400 uppercase tracking-widest"
          >Description</span
        >
        <span class="text-[10px] font-black text-gray-400 uppercase tracking-widest"
          >Amount (MMK)</span
        >
      </div>
      <div class="flex justify-between items-end">
        <div>
          <h3 class="text-[14px] font-black text-gray-900 uppercase italic mb-2">
            {{ repair.item_name }}
          </h3>
          <p class="text-gray-500 font-bold text-[12px] leading-tight">
            {{ repair.problem_description }}
          </p>
        </div>
        <span class="text-[16px] font-black text-gray-900 font-mono tracking-tighter">
          {{ Math.round(Number(repair.total_estimated_cost) || 0).toLocaleString(undefined, { maximumFractionDigits: 0 }) }}
        </span>
      </div>
    </div>

    <!-- Spare Parts: backend GET/POST service/repairs/<id>/spare-parts/ -->
    <div class="border border-gray-200 rounded-xl p-4 mb-5 relative z-10">
      <h3 class="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-3">Spare Parts</h3>
      <div class="max-h-40 overflow-y-auto border border-gray-100 rounded-lg mb-3">
        <table class="w-full text-[12px]">
          <thead class="bg-gray-100 sticky top-0">
            <tr>
              <th class="text-left py-2 px-2 font-bold text-gray-600">Part</th>
              <th class="text-right py-2 px-2 font-bold text-gray-600">Qty</th>
              <th class="text-right py-2 px-2 font-bold text-gray-600">Unit</th>
              <th class="text-right py-2 px-2 font-bold text-gray-600">Subtotal</th>
              <th class="w-10 print:hidden"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in sparePartsList" :key="p.id" class="border-t border-gray-100">
              <td class="py-1.5 px-2 text-gray-900">{{ p.part_name || '–' }}</td>
              <td class="py-1.5 px-2 text-right font-mono">{{ p.quantity }}</td>
              <td class="py-1.5 px-2 text-right font-mono">{{ Math.round(Number(p.unit_price) || 0).toLocaleString(undefined, { maximumFractionDigits: 0 }) }}</td>
              <td class="py-1.5 px-2 text-right font-mono font-bold">{{ Math.round(Number(p.subtotal) || 0).toLocaleString(undefined, { maximumFractionDigits: 0 }) }}</td>
              <td class="py-1.5 print:hidden">
                <button type="button" class="text-rose-600 hover:underline text-[10px] font-bold" @click="removeSparePart(p.id)">Remove</button>
              </td>
            </tr>
            <tr v-if="sparePartsList.length === 0">
              <td colspan="5" class="py-4 text-center text-gray-400 text-[12px]">No spare parts</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="print:hidden flex flex-wrap gap-2 items-end">
        <input v-model="newPart.part_name" placeholder="Part name" class="border border-gray-300 rounded px-2 py-1.5 text-[12px] w-32" />
        <input v-model.number="newPart.quantity" type="number" min="1" placeholder="Qty" class="border border-gray-300 rounded px-2 py-1.5 text-[12px] w-20" />
        <input v-model.number="newPart.unit_price" type="number" min="0" step="1" placeholder="Unit price (MMK)" class="border border-gray-300 rounded px-2 py-1.5 text-[12px] w-24" />
        <button type="button" class="bg-gray-900 text-white px-3 py-1.5 rounded text-[12px] font-bold" @click="addSparePart">Add</button>
      </div>
    </div>

    <div class="flex justify-end mb-20 relative z-10">
      <div class="w-80 space-y-4">
        <div
          class="flex justify-between text-[12px] font-black text-gray-400 uppercase tracking-widest px-2"
        >
          <span>Subtotal</span>
          <span class="text-gray-900 font-mono">{{
            Math.round(Number(repair.total_estimated_cost) || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })
          }}</span>
        </div>
        <div
          class="flex justify-between text-[12px] font-black text-blue-600 p-4 rounded-2xl border border-blue-100"
        >
          <span>Deposit Paid (-)</span>
          <span class="font-mono">- {{ Math.round(Number(repair.deposit_amount) || 0).toLocaleString(undefined, { maximumFractionDigits: 0 }) }}</span>
        </div>
        <div
          class="flex justify-between text-[16px] border-t-4 border-gray-900 pt-6 font-black uppercase italic tracking-tighter -mt-2"
        >
          <span>{{ repair.status === 'completed' ? 'TOTAL PAID' : 'BALANCE' }}</span>
          <span class="font-mono decoration-double text-red-600">
            {{ Math.round(Number(repair.balance_amount) || 0).toLocaleString(undefined, { maximumFractionDigits: 0 }) }}
          </span>
        </div>
      </div>
    </div>

    <div class="mt-auto grid grid-cols-2 gap-32 text-center px-10">
      <div
        class="border-t-2 border-gray-300 pt-5 text-xs font-black uppercase text-gray-400 tracking-widest"
      >
        Customer
      </div>
      <div
        class="border-t-2 border-gray-300 pt-5 text-xs font-black uppercase text-gray-400 tracking-widest"
      >
        Authorized Sign
      </div>
    </div>

    <div class="print:hidden mt-10 flex flex-wrap gap-4 relative z-50">
      <button
        v-if="repair.status === 'received'"
        @click="updateStatus('ready')"
        class="bg-blue-600 text-white px-6 py-3 rounded-xl font-black shadow-lg hover:bg-blue-700"
      >
        MARK AS READY
      </button>

      <button
        v-if="repair.status === 'ready'"
        @click="updateStatus('completed')"
        class="bg-green-600 text-white px-6 py-3 rounded-xl font-black shadow-lg hover:bg-green-700"
      >
        DELIVER & PAID
      </button>

      <button
        @click="handlePrint"
        class="bg-gray-900 text-white px-10 py-4 rounded-2xl font-black shadow-xl hover:scale-105 transition-transform"
      >
        🖨️ PRINT INVOICE
      </button>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits, computed, ref, watch } from 'vue'
import axios from 'axios'
import { API_URL } from '@/config'
import api from '@/services/api'
import { useShopSettingsStore } from '@/stores/shopSettings'

const shopStore = useShopSettingsStore()
const logoImage = computed(() => shopStore.logo_url || (import.meta.env.BASE_URL || '/') + 'logo.svg')
const shopName = computed(() => shopStore.displayName)

const props = defineProps({ repair: { type: Object, required: true } })
const emit = defineEmits(['updated'])

const sparePartsList = ref([])
const newPart = ref({ part_name: '', quantity: 1, unit_price: 0 })

function setSparePartsFromRepair(repair) {
  sparePartsList.value = repair?.spare_parts ?? []
}

watch(() => props.repair, (r) => {
  setSparePartsFromRepair(r)
  if (r?.id && (r.spare_parts == null || !Array.isArray(r.spare_parts))) fetchSpareParts()
}, { immediate: true })

async function fetchSpareParts() {
  if (!props.repair?.id) return
  try {
    const res = await api.get(`service/repairs/${props.repair.id}/spare-parts/`)
    sparePartsList.value = res.data || []
  } catch {
    sparePartsList.value = []
  }
}

async function addSparePart() {
  if (!props.repair?.id || !newPart.value.part_name?.trim()) return
  try {
    await api.post(`service/repairs/${props.repair.id}/spare-parts/`, {
      part_name: newPart.value.part_name.trim(),
      quantity: Number(newPart.value.quantity) || 1,
      unit_price: Number(newPart.value.unit_price) || 0,
    })
    newPart.value = { part_name: '', quantity: 1, unit_price: 0 }
    const detail = await api.get(`service/repairs/${props.repair.id}/`)
    setSparePartsFromRepair(detail.data)
    emit('updated', detail.data)
  } catch (e) {
    console.error(e)
  }
}

async function removeSparePart(partId) {
  if (!props.repair?.id || !partId) return
  try {
    await api.delete(`service/repairs/${props.repair.id}/spare-parts/${partId}/`)
    const detail = await api.get(`service/repairs/${props.repair.id}/`)
    setSparePartsFromRepair(detail.data)
    emit('updated', detail.data)
  } catch (e) {
    console.error(e)
  }
}

const updateStatus = async (newStatus) => {
  try {
    const res = await axios.patch(
      `${API_URL}service/repairs/${props.repair.id}/`,
      { status: newStatus },
      { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } },
    )
    emit('updated', res.data)
    setSparePartsFromRepair(res.data)
  } catch (err) {
    console.error(err)
  }
}
const handlePrint = () => {
  window.print()
}
</script>

<style scoped>
#printable-invoice {
  width: 5.8in;
  min-height: 297mm;
  padding: 25mm;
  background: white;
}

@media print {
  @page {
    size: portrait;
    margin: 0 !important;
  }
  body * {
    visibility: hidden !important;
  }
  #printable-invoice,
  #printable-invoice * {
    visibility: visible !important;
  }
  #printable-invoice {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 5.8in !important;
    height: 100% !important;
    margin: 0 !important;
    padding: 15mm !important;
    border: none !important;
    box-shadow: none !important;
    z-index: 9999;
  }
  /* Vue DevTools ကို လုံးဝဖျောက်ခြင်း */
  [class*='vue-devtools'],
  [data-v-inspector],
  #vue-devtools-anchor,
  button,
  .print\:hidden {
    display: none !important;
    visibility: hidden !important;
  }
}
</style>
