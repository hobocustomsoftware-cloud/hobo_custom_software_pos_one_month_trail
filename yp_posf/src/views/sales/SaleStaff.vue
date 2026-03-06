<template>
  <div id="invoice-print-area" v-if="selectedSale" class="print-only font-sans">
    <div class="invoice-wrapper">
      <div class="header-grid">
        <div class="company-brand">
          <h1 class="brand-name">WELDING PRO SOLUTIONS</h1>
          <p class="brand-sub">ဂဟေဆော်စက်နှင့် ဆက်စပ်ပစ္စည်း အရောင်းဌာန</p>
          <div class="contact-info">
            <p>အမှတ် (၁၂၃)၊ လမ်းမတော်၊ ရန်ကုန်မြို့။</p>
            <p>ဖုန်း - ၀၉ ၇၉၉ ၉၉၉ ၉၉၉</p>
          </div>
        </div>
        <div class="invoice-info text-right">
          <h2 class="title-label">Sales Invoice</h2>
          <div class="meta-row">
            <span class="label">Voucher No:</span>
            <span class="value">{{ selectedSale.invoice_number || selectedSale.id }}</span>
          </div>
          <div class="meta-row">
            <span class="label">Date:</span>
            <span class="value">{{ formatDate(selectedSale.created_at) }}</span>
          </div>
          <div class="meta-row">
            <span class="label">Status:</span>
            <span class="value uppercase font-bold text-blue-600">{{ selectedSale.status }}</span>
          </div>
        </div>
      </div>

      <div class="customer-box">
        <h4 class="section-title">Bill To:</h4>
        <p class="customer-name">{{ selectedSale.customer_name || 'Cash Customer' }}</p>
        <p class="customer-detail">{{ selectedSale.customer_phone || '-' }}</p>
      </div>

      <table class="invoice-table">
        <thead>
          <tr>
            <th class="text-left">Description</th>
            <th class="text-center">Qty</th>
            <th class="text-right">Unit Price</th>
            <th class="text-right">Amount</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in selectedSale.sale_items" :key="item.id">
            <td>
              <div class="product-title">{{ item.product_name }}</div>
              <div v-if="item.serial_number" class="serial-tag">S/N: {{ item.serial_number }}</div>
            </td>
            <td class="text-center">{{ item.quantity }}</td>
            <td class="text-right">{{ formatNumber(item.unit_price) }}</td>
            <td class="text-right">{{ formatNumber(item.quantity * item.unit_price) }}</td>
          </tr>
        </tbody>
        <tfoot>
          <tr>
            <td colspan="3" class="text-right">Total Amount</td>
            <td class="text-right">{{ formatNumber(selectedSale.total_amount) }}</td>
          </tr>
          <tr v-if="selectedSale.discount_amount > 0" class="text-red-600">
            <td colspan="3" class="text-right font-bold">Discount (-)</td>
            <td class="text-right font-bold">{{ formatNumber(selectedSale.discount_amount) }}</td>
          </tr>
          <tr class="net-amount-row">
            <td colspan="3" class="text-right font-black uppercase">Net Amount (MMK)</td>
            <td class="text-right font-black">
              {{ formatNumber(selectedSale.total_amount - selectedSale.discount_amount) }}
            </td>
          </tr>
        </tfoot>
      </table>

      <div class="signature-section">
        <div class="sig-field">
          <div class="sig-line"></div>
          <p>Customer's Signature</p>
        </div>
        <div class="sig-field">
          <div class="sig-line"></div>
          <p>Authorized Signature</p>
        </div>
      </div>

      <div class="thanks-note">
        <p>ဝယ်ယူအားပေးမှုကို အထူးကျေးဇူးတင်ရှိပါသည်။</p>
        <p class="small text-gray-400">Software Generated Invoice</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Screen ပေါ်မှာ လုံးဝဖျောက်ထားရန် */
@media screen {
  .print-only {
    display: none !important;
  }
}

/* Print ထုတ်ချိန် Styling */
@media print {
  body * {
    visibility: hidden;
  }
  .print-only,
  .print-only * {
    visibility: visible;
  }
  .print-only {
    display: block !important;
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
    color: #000;
  }
  @page {
    size: A4;
    margin: 1.5cm;
  }
}

.invoice-wrapper {
  padding: 10px;
  border: 1px solid #eee;
}
.header-grid {
  display: flex;
  justify-content: space-between;
  border-bottom: 3px solid #1a1a1a;
  padding-bottom: 15px;
  margin-bottom: 25px;
}
.brand-name {
  font-size: 26px;
  font-weight: 900;
  margin: 0;
  letter-spacing: -1px;
}
.brand-sub {
  font-size: 14px;
  font-weight: bold;
  margin: 2px 0;
}
.contact-info p {
  font-size: 11px;
  margin: 0;
  color: #444;
}

.title-label {
  font-size: 22px;
  font-weight: 900;
  color: #2563eb;
  text-transform: uppercase;
  margin-bottom: 10px;
}
.meta-row {
  font-size: 12px;
  margin-bottom: 3px;
}
.meta-row .label {
  font-weight: bold;
  color: #666;
  margin-right: 5px;
}

.customer-box {
  margin-bottom: 25px;
}
.section-title {
  font-size: 11px;
  text-transform: uppercase;
  color: #888;
  font-weight: 900;
  margin-bottom: 5px;
}
.customer-name {
  font-size: 16px;
  font-weight: 800;
  margin: 0;
}

.invoice-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 30px;
}
.invoice-table th {
  background: #f8fafc;
  border: 1px solid #000;
  padding: 10px;
  font-size: 12px;
  font-weight: 900;
  text-transform: uppercase;
}
.invoice-table td {
  border: 1px solid #e2e8f0;
  padding: 10px;
  vertical-align: top;
}
.product-title {
  font-weight: 800;
  font-size: 14px;
}
.serial-tag {
  font-family: monospace;
  font-size: 11px;
  color: #555;
  background: #f1f5f9;
  padding: 2px 4px;
  display: inline-block;
  margin-top: 4px;
}

.net-amount-row {
  background: #f1f5f9 !important;
  font-size: 15px;
}
.net-amount-row td {
  border: 1px solid #000 !important;
}

.signature-section {
  display: flex;
  justify-content: space-between;
  margin-top: 80px;
  padding: 0 20px;
}
.sig-field {
  text-align: center;
  width: 200px;
}
.sig-line {
  border-top: 1.5px solid #000;
  margin-bottom: 8px;
}
.sig-field p {
  font-size: 12px;
  font-weight: 900;
  text-transform: uppercase;
}

.thanks-note {
  text-align: center;
  margin-top: 50px;
  border-top: 1px dashed #ccc;
  padding-top: 15px;
}
.thanks-note p {
  font-size: 13px;
  font-weight: bold;
}
.small {
  font-size: 10px;
}
</style>

<script setup>
import { ref } from 'vue'

const selectedSale = ref(null)

// Print လုပ်ရန် ခေါ်ရမည့် function
const triggerPrint = (saleData) => {
  selectedSale.value = saleData
  // UI update ဖြစ်စေရန် ခေတ္တစောင့်ပြီးမှ print window ဖွင့်မည်
  setTimeout(() => {
    window.print()
  }, 200)
}

const formatNumber = (num) => {
  if (!num) return '0'
  return Number(num).toLocaleString('en-US')
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

// ပြင်ပမှ ခေါ်သုံးနိုင်ရန် export လုပ်ထားနိုင်သည်
defineExpose({ triggerPrint })
</script>
