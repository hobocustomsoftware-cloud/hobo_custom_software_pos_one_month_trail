<template>
  <div
    id="invoice-print-area"
    v-if="sale"
    class="hidden print:block w-full text-black p-4 relative h-full invoice-print-myanmar"
  >
    <div class="flex justify-between items-start border-b-2 border-black pb-3 mb-4">
      <div class="flex flex-col gap-1">
        <img v-if="logoBase64" :src="logoBase64" class="w-12 h-auto mb-1" />
        <h1 class="text-[13px] font-black uppercase">{{ shopName }}</h1>
        <p class="text-[8px] font-bold text-gray-700">ဂဟေဆော်စက်နှင့် ဆက်စပ်ပစ္စည်း အရောင်းဆိုင်</p>
        <p class="text-[8px] font-bold text-gray-700">အမှတ် ၁၈/၉ လမ်းမတော်လမ်း</p>
        <p class="text-[8px] font-bold text-gray-700">ဖုန်း - 0932214001</p>
      </div>
      <div class="text-right">
        <h2 class="text-xl font-black text-blue-700 leading-none mb-1">INVOICE</h2>
        <div class="text-[9px] space-y-0.5">
          <p><b>No:</b> #{{ sale.invoice_number }}</p>
          <p><b>Date:</b> {{ formatDate(sale.created_at) }}</p>
        </div>
      </div>
    </div>

    <div class="mb-4">
      <span class="text-[9px] font-bold text-gray-400 uppercase tracking-widest">Bill To:</span>
      <p class="text-[13px] font-black mt-1 pl-2 border-l-2 border-gray-200">
        {{
          sale.customer_name && sale.customer_name !== 'Cash Customer' ? sale.customer_name : '-'
        }}
      </p>
    </div>

    <table class="w-full border-collapse border border-black mb-4 text-[10px]">
      <thead class="bg-gray-100 uppercase">
        <tr>
          <th class="border border-black p-2 text-left">Description</th>
          <th class="border border-black p-2 text-center w-12">Qty</th>
          <th class="border border-black p-2 text-right w-24">Amount</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in sale.sale_items" :key="item.id">
          <td class="border border-black p-2 font-bold leading-tight">{{ item.product_name }}</td>
          <td class="border border-black p-2 text-center">{{ item.quantity }}</td>
          <td class="border border-black p-2 text-right font-bold">
            {{ formatNumber(item.subtotal) }}
          </td>
        </tr>
      </tbody>
      <tfoot>
        <tr class="bg-gray-50 font-black">
          <td colspan="2" class="border border-black p-2 text-right uppercase text-[9px]">
            Net Amount (MMK)
          </td>
          <td class="border border-black p-2 text-right text-blue-800 text-[12px]">
            {{ formatNumber(sale.total_amount || calculateTotal(sale.sale_items)) }}
          </td>
        </tr>
      </tfoot>
    </table>

    <div class="mt-28 relative h-20">
      <div v-if="sale.status === 'approved'" class="paid-stamp-portrait">PAID</div>

      <div class="flex justify-between items-end relative z-10 h-full">
        <div class="w-32 text-center border-t border-black pt-1">
          <span class="text-[9px] font-black uppercase tracking-tighter">Customer Signature</span>
        </div>

        <div class="w-40 text-center">
          <p class="text-[8px] italic mb-1 text-gray-500">
            Issued by: {{ sale.staff_name || 'admin' }}
          </p>
          <div class="border-t border-black pt-1">
            <span class="text-[9px] font-black uppercase tracking-tighter block"
              >Authorized Seller</span
            >
          </div>
        </div>
      </div>
    </div>

    <p class="text-center mt-12 text-[9px] font-bold italic border-t pt-2 text-gray-400 uppercase">
      Thank you for your business!
    </p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useShopSettingsStore } from '@/stores/shopSettings'

const shopStore = useShopSettingsStore()
const logoImage = computed(() => shopStore.logo_url || (import.meta.env.BASE_URL || '/') + 'logo.svg')
const shopName = computed(() => shopStore.displayName)

const props = defineProps(['sale'])
const logoBase64 = ref('')

const formatNumber = (val) => {
  if (!val || val === '0.00' || val === 0) return '0'
  return Math.round(Number(val) || 0).toLocaleString(undefined, { maximumFractionDigits: 0, minimumFractionDigits: 0 })
}

const formatDate = (d) => (d ? new Date(d).toLocaleDateString('en-GB') : '-')

const calculateTotal = (items) => {
  if (!items) return 0
  return items.reduce((sum, item) => sum + parseFloat(item.subtotal || 0), 0)
}

onMounted(() => {
  const img = new Image()
  img.src = logoImage.value
  img.onload = () => {
    const canvas = document.createElement('canvas')
    canvas.width = img.width
    canvas.height = img.height
    const ctx = canvas.getContext('2d')
    ctx.drawImage(img, 0, 0)
    logoBase64.value = canvas.toDataURL('image/png')
  }
})
</script>

<style scoped>
@media print {
  @page {
    size: A5 portrait !important;
    margin: 0.8cm !important;
  }
  #invoice-print-area {
    display: block !important;
    width: 100% !important;
  }
}

.paid-stamp-portrait {
  border: 4px double #ef4444;
  color: #ef4444;
  font-size: 28px;
  font-weight: 900;
  padding: 2px 15px;
  border-radius: 4px;
  opacity: 0.4;
  /* ⚠️ အလယ်တည့်တည့် ရောက်စေရန် Position ညှိချက် */
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%) rotate(-15deg);
  z-index: 5;
}
</style>
