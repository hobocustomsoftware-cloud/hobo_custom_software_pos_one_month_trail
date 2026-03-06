<template>
  <div
    v-if="show"
    class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50"
    @click.self="$emit('close')"
  >
    <div class="bg-bg rounded-2xl shadow-xl border border-border max-w-lg w-full p-6">
      <h3 class="pos-text font-semibold text-fg mb-4">အမှတ်စဉ် (IMEI/Batch) ရိုက်ထည့်ပါ</h3>
      <input
        ref="inputRef"
        v-model="serialValue"
        type="text"
        class="w-full min-h-[80px] px-6 text-[25px] font-semibold text-fg bg-bg border border-border rounded-xl outline-none focus:ring-2 focus:ring-green-500 leading-myanmar font-myanmar"
        placeholder="IMEI သို့မဟုတ် Batch နံပါတ်"
        autofocus
        @keyup.enter="confirm"
      />
      <div class="flex gap-4 mt-6">
        <button
          type="button"
          class="flex-1 pos-btn bg-gray-200 text-fg hover:bg-gray-300 leading-myanmar"
          @click="$emit('close')"
        >
          ပယ်ဖျက်မည်
        </button>
        <button
          type="button"
          class="flex-1 pos-btn pos-btn-pay leading-myanmar"
          :disabled="!serialValue.trim()"
          @click="confirm"
        >
          အတည်ပြုမည်
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({ show: { type: Boolean, default: false } })
const emit = defineEmits(['close', 'confirm'])

const serialValue = ref('')
const inputRef = ref(null)

function focusInput() {
  nextTick(() => {
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        inputRef.value?.focus()
      })
    })
  })
}

watch(() => props.show, (v) => {
  if (v) {
    serialValue.value = ''
    focusInput()
  }
})

function confirm() {
  const v = serialValue.value?.trim()
  if (!v) return
  emit('confirm', v)
  emit('close')
}
</script>
