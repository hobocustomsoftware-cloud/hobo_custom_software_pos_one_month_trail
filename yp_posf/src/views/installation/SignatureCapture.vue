<template>
  <div class="space-y-4">
    <div class="glass-card p-4">
      <label class="glass-label block mb-2">Draw Signature</label>
      <canvas
        ref="canvasRef"
        @mousedown="startDrawing"
        @mousemove="draw"
        @mouseup="stopDrawing"
        @mouseleave="stopDrawing"
        class="border border-white/20 rounded bg-white cursor-crosshair"
        width="600"
        height="200"
      />
      <div class="flex gap-2 mt-4">
        <button
          @click="clearCanvas"
          class="px-4 py-2 bg-white/10 text-white/90 rounded-xl hover:bg-white/20"
        >
          Clear
        </button>
        <button
          @click="saveSignature"
          :disabled="disabled || !hasSignature"
          class="px-4 py-2 bg-blue-500 text-white rounded-xl font-bold hover:bg-blue-600 disabled:opacity-50"
        >
          Save Signature
        </button>
      </div>
    </div>

    <div class="glass-card p-4">
      <label class="glass-label block mb-2">Or Upload Signature Image</label>
      <input
        type="file"
        accept="image/*"
        @change="handleFileUpload"
        :disabled="disabled"
        class="glass-input w-full px-4 py-2"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
  disabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['signature-captured'])

const canvasRef = ref(null)
const isDrawing = ref(false)
const hasSignature = ref(false)

let ctx = null

onMounted(() => {
  if (canvasRef.value) {
    ctx = canvasRef.value.getContext('2d')
    ctx.strokeStyle = '#000000'
    ctx.lineWidth = 2
    ctx.lineCap = 'round'
  }
})

const startDrawing = (e) => {
  if (props.disabled) return
  isDrawing.value = true
  const rect = canvasRef.value.getBoundingClientRect()
  ctx.beginPath()
  ctx.moveTo(e.clientX - rect.left, e.clientY - rect.top)
}

const draw = (e) => {
  if (!isDrawing.value || props.disabled) return
  const rect = canvasRef.value.getBoundingClientRect()
  ctx.lineTo(e.clientX - rect.left, e.clientY - rect.top)
  ctx.stroke()
  hasSignature.value = true
}

const stopDrawing = () => {
  isDrawing.value = false
}

const clearCanvas = () => {
  if (props.disabled) return
  ctx.clearRect(0, 0, canvasRef.value.width, canvasRef.value.height)
  hasSignature.value = false
}

const saveSignature = () => {
  if (props.disabled || !hasSignature.value) return
  
  canvasRef.value.toBlob((blob) => {
    const file = new File([blob], 'signature.png', { type: 'image/png' })
    emit('signature-captured', file)
  }, 'image/png')
}

const handleFileUpload = (e) => {
  if (props.disabled) return
  const file = e.target.files?.[0]
  if (file) {
    emit('signature-captured', file)
  }
}
</script>
