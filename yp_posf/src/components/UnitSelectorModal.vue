<template>
  <div
    v-if="show"
    class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50"
    @click.self="$emit('close')"
  >
    <div class="bg-bg rounded-[12px] shadow-xl border border-border max-w-lg w-full p-6">
      <h3 class="pos-text font-semibold text-fg mb-4" style="font-size: 25px;">
        {{ mode === 'hardware' ? 'ယူနစ်ရွေးချယ်ပါ (ခု/ဒါဇင်/ဖာ/ပေ/မီတာ/ပိတ်သာ)' : 'ယူနစ်ရွေးချယ်ပါ (လုံး/ကဒ်/ဗူး/ပုလင်း)' }}
      </h3>

      <!-- Hardware: decimal quantity + unit (Loyverse-style modal) -->
      <template v-if="mode === 'hardware'">
        <div class="mb-4">
          <label class="block text-fg-muted font-semibold mb-2 pos-text">ပမာဏ (ဒဿမပါ ထည့်နိုင်သည်)</label>
          <input
            v-model.number="hardwareQty"
            type="number"
            min="1"
            step="1"
            class="w-full min-h-[80px] px-4 text-[25px] font-semibold text-fg bg-bg border border-border rounded-[12px]"
            placeholder="ဥပမာ 1 သို့ 10"
          />
        </div>
        <div class="flex flex-col gap-3 mb-4">
          <button
            v-for="(opt, idx) in hardwareOptions"
            :key="opt.value"
            :ref="(el) => { if (idx === 0) firstOptionRef.value = el }"
            type="button"
            class="w-full text-left px-6 py-4 bg-bg-card border rounded-[12px] text-fg font-semibold leading-myanmar transition-colors min-h-[80px] flex items-center"
            :class="selectedUnit === opt.value ? 'border-[#1078D1] bg-[#1078D1]/10 ring-2 ring-[#1078D1]/30' : 'border-border hover:border-[#1078D1]/50 hover:bg-[#1078D1]/5'"
            @click="selectedUnit = opt.value"
          >
            <span style="font-size: 25px;">{{ opt.label }}</span>
            <span v-if="opt.factor !== 1" class="text-fg-muted text-[20px] ml-2">({{ opt.factor }} ခု)</span>
          </button>
        </div>
        <div class="flex gap-2">
          <button
            type="button"
            class="flex-1 min-h-[80px] text-[25px] font-semibold text-white rounded-[12px] leading-myanmar bg-[#1078D1] hover:bg-[#0d62a8] disabled:opacity-50"
            :disabled="!isHardwareValid"
            @click="confirmHardware"
          >
            ထည့်မည်
          </button>
          <button
            type="button"
            class="min-h-[80px] px-6 text-[25px] text-fg bg-gray-200 hover:bg-gray-300 rounded-[12px] leading-myanmar"
            @click="$emit('close')"
          >
            ပယ်ဖျက်မည်
          </button>
        </div>
      </template>

      <!-- Pharmacy: unit buttons only (quantity = 1) -->
      <template v-else>
        <div class="flex flex-col gap-3">
          <button
            v-for="(opt, idx) in pharmacyOptions"
            :key="opt.value"
            :ref="(el) => { if (idx === 0) firstOptionRef.value = el }"
            type="button"
            class="w-full text-left px-6 min-h-[80px] flex items-center bg-bg-card border border-border rounded-[12px] text-fg font-semibold hover:border-[#1078D1] hover:bg-[#1078D1]/5 leading-myanmar"
            style="font-size: 25px;"
            @click="select(opt.value)"
          >
            {{ opt.label }}
          </button>
        </div>
        <button
          type="button"
          class="w-full min-h-[80px] mt-4 text-[25px] bg-gray-200 text-fg hover:bg-gray-300 rounded-[12px] leading-myanmar"
          @click="$emit('close')"
        >
          ပယ်ဖျက်မည်
        </button>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { HARDWARE_UNITS } from '@/utils/hardwareUnits'

const props = defineProps({
  show: { type: Boolean, default: false },
  /** Pharmacy = လုံး/ကဒ်/ဗူး/ပုလင်း. Hardware = ခု/ဒါဇင်/ဖာ/ပေ/မီတာ/ပိတ်သာ with fractional qty */
  mode: { type: String, default: 'pharmacy' },
})
const emit = defineEmits(['close', 'select'])

const firstOptionRef = ref(null)
const hardwareQty = ref(1)
const selectedUnit = ref('piece')

const hardwareOptions = computed(() =>
  HARDWARE_UNITS.map((u) => ({ value: u.value, label: u.label, factor: u.factor }))
)

const pharmacyOptions = [
  { value: 'piece', label: 'လုံး (Pieces)' },
  { value: 'strip', label: 'တစ်ကတ် (Strip)' },
  { value: 'box', label: 'ဗူး (Box)' },
  { value: 'bottle', label: 'ပုလင်း (တစ်ပုလင်း၊ နှစ်ပုလင်း)' },
]

const isHardwareValid = computed(() => {
  const q = Number(hardwareQty.value)
  return !Number.isNaN(q) && q >= 1
})

function focusFirstOption() {
  nextTick(() => {
    requestAnimationFrame(() => {
      if (firstOptionRef.value && typeof firstOptionRef.value.focus === 'function') {
        firstOptionRef.value.focus()
      }
    })
  })
}

watch(
  () => props.show,
  (v) => {
    if (v) {
      hardwareQty.value = 1
      selectedUnit.value = 'piece'
      nextTick(() => {
        setTimeout(() => focusFirstOption(), 150)
      })
    }
  }
)

function select(value) {
  emit('select', value)
  emit('close')
}

function confirmHardware() {
  if (!isHardwareValid.value) return
  const qty = Number(hardwareQty.value)
  emit('select', { unit: selectedUnit.value, quantity: qty })
  emit('close')
}
</script>
