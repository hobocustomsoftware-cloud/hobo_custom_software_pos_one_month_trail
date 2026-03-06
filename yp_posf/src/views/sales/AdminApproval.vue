<template>
  <div class="layout-container font-sans bg-[#f4f4f4] min-h-full">
    <div class="max-w-7xl mx-auto">
      <div class="flex flex-wrap justify-between items-center mb-6" style="gap: var(--fluid-gap);">
        <div>
          <h1 class="text-fluid-xl font-black uppercase tracking-tight text-[#1a1a1a]">Sale Requests</h1>
          <p class="text-fluid-sm font-medium text-[#6b7280] uppercase mt-1">
            အရောင်းတောင်းဆိုမှုများကို စစ်ဆေးအတည်ပြုရန် သို့မဟုတ် ငြင်းပယ်ရန်
          </p>
        </div>
        <button
          @click="fetchPendingSales"
          class="btn-secondary flex items-center gap-2 px-4 py-2.5 interactive"
        >
          🔄 Refresh
        </button>
      </div>

      <div class="bg-white rounded-xl border border-[var(--color-border)] shadow-sm overflow-hidden">
        <div class="overflow-x-auto custom-scrollbar">
          <table class="w-full">
            <thead class="bg-[var(--color-bg-card)] border-b border-[var(--color-border)]">
              <tr>
                <th class="p-4 text-left text-xs font-bold text-[#6b7280] uppercase">Date</th>
                <th class="p-4 text-left text-xs font-bold text-[#6b7280] uppercase">Order Items</th>
                <th class="p-4 text-left text-xs font-bold text-[#6b7280] uppercase">Staff / Location</th>
                <th class="p-4 text-center text-xs font-bold text-[#6b7280] uppercase">Decision</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-[var(--color-border)]">
              <tr
                v-for="sale in pendingSales"
                :key="sale.id"
                class="interactive hover:bg-[var(--color-bg-card)]"
              >
                <td class="p-4 text-fluid-sm font-medium text-[#4b5563]">
                  {{ formatDate(sale.created_at) }}
                </td>
                <td class="p-4">
                  <div
                    v-for="item in sale.sale_items"
                    :key="item.id"
                    class="mb-2 border-l-4 border-[#aa0000]/40 pl-3"
                  >
                    <div class="font-semibold text-[#1a1a1a] text-fluid-sm uppercase">
                      {{ item.product_name || item.product?.name }}
                    </div>
                    <div class="text-fluid-sm font-medium text-blue-600">
                      Qty: {{ item.quantity }} | S/N: {{ item.serial_number || 'N/A' }}
                    </div>
                  </div>
                </td>
                <td class="p-4">
                  <div class="text-fluid-sm font-semibold text-[#1a1a1a] uppercase">{{ sale.staff_name }}</div>
                  <div class="text-fluid-sm text-[#6b7280] font-medium">
                    📍 {{ sale.location_name || 'Main Office' }}
                  </div>
                </td>
                <td class="p-4">
                  <div class="flex flex-col gap-2 items-center">
                    <button
                      @click="handleAction(sale.id, 'approve')"
                      class="w-32 btn-primary py-2.5 text-fluid-sm interactive"
                    >
                      ✅ Approve
                    </button>
                    <button
                      @click="handleAction(sale.id, 'reject')"
                      class="w-32 btn-secondary py-2.5 text-fluid-sm text-rose-600 hover:text-rose-700 interactive"
                    >
                      ❌ Reject
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div
          v-if="pendingSales.length === 0"
          class="p-20 text-center text-[#6b7280] font-semibold uppercase text-fluid-sm"
        >
          စစ်ဆေးရန် အရောင်းစာရင်းမရှိပါ။
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

const pendingSales = ref([])

const fetchPendingSales = async () => {
  try {
    // api service က auto token injection လုပ်ပေးတယ်
    const res = await api.get('admin/pending/')
    pendingSales.value = res.data
  } catch (err) {
    console.error('Fetch error:', err)
  }
}

// Approve နှင့် Reject နှစ်မျိုးလုံးကို ကိုင်တွယ်မည့် Function
const handleAction = async (id, type) => {
  let reason = ''

  if (type === 'reject') {
    reason = prompt(
      'ငြင်းပယ်ရသည့် အကြောင်းရင်းကို ရေးပေးပါ (ဥပမာ- Serial number မှားယွင်းနေပါသည်) -',
    )
    if (!reason) return // Cancel နှိပ်ရင် ဘာမှမလုပ်ပါ
  } else {
    if (!confirm('အတည်ပြုရန် သေချာပါသလား?')) return
  }

  try {
    // api service က auto token injection လုပ်ပေးတယ်
    await api.patch(`admin/approve/${id}/`, {
      status: type === 'approve' ? 'approved' : 'rejected',
      reject_reason: reason,
    })

    alert(type === 'approve' ? 'Approved Successfully' : 'Rejected Successfully')
    fetchPendingSales()
  } catch (err) {
    alert('Error: ' + (err.response?.data?.error || 'လုပ်ဆောင်ချက် မအောင်မြင်ပါ'))
  }
}

const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleString('en-GB', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(fetchPendingSales)
</script>
