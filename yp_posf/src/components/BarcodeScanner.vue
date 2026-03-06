<template>
  <div v-if="show" class="fixed inset-0 z-[200] flex flex-col bg-black">
    <div id="barcode-scanner-area" class="flex-1 relative min-h-[300px]">
      <!-- html5-qrcode renders camera here -->
    </div>
    <div class="p-4 bg-gray-900 flex gap-3">
      <button
        @click="stopScan"
        class="flex-1 py-3 bg-[#aa0000] hover:bg-[#cc0000] text-white font-bold rounded-xl transition-colors"
      >
        ပိတ်မည်
      </button>
      <button
        @click="manualInput"
        class="flex-1 py-3 bg-[#aa0000]/90 hover:bg-[#cc0000] text-white font-bold rounded-xl transition-colors"
      >
        ကိုယ်တိုင် ရိုက်ထည့်မည်
      </button>
    </div>
    <div v-if="showManualInput" class="p-4 bg-gray-800">
      <input
        ref="manualInputRef"
        v-model="manualValue"
        type="text"
        placeholder="SKU / Barcode ရိုက်ထည့်ပါ"
        class="w-full p-4 rounded-xl border-2 border-[#aa0000]/60 text-lg text-white bg-gray-700 focus:border-[#aa0000] outline-none"
        @keyup.enter="submitManual"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted, watch } from 'vue'
import { Html5Qrcode, Html5QrcodeSupportedFormats } from 'html5-qrcode'

const props = defineProps({
  show: { type: Boolean, default: false },
})

const emit = defineEmits(['scan', 'close'])

const manualInputRef = ref(null)
const showManualInput = ref(false)
const manualValue = ref('')

let html5QrCode = null

const startScan = async () => {
  if (!props.show) return
  const el = document.getElementById('barcode-scanner-area')
  if (!el) return
  if (html5QrCode && html5QrCode.isScanning) {
    try { await html5QrCode.stop() } catch (_) {}
    html5QrCode = null
  }
  // QR + standard + slim barcodes (IMEI etc.): CODE_128, ITF, CODE_39/93
const scanConfig = {
  fps: 10,
  qrbox: { width: 260, height: 200 },
  aspectRatio: 1.3,
  formatsToSupport: [
    Html5QrcodeSupportedFormats.QR_CODE,
    Html5QrcodeSupportedFormats.EAN_13,
    Html5QrcodeSupportedFormats.EAN_8,
    Html5QrcodeSupportedFormats.CODE_128,
    Html5QrcodeSupportedFormats.CODE_39,
    Html5QrcodeSupportedFormats.CODE_93,
    Html5QrcodeSupportedFormats.UPC_A,
    Html5QrcodeSupportedFormats.UPC_E,
    Html5QrcodeSupportedFormats.ITF,
  ],
}
  const onSuccess = (decodedText) => handleScanResult(decodedText)
  const onFail = () => {}

  try {
    html5QrCode = new Html5Qrcode('barcode-scanner-area')

    // 1) Try each available camera by ID (laptop webcam, external, phone back/front အကုန်ဖတ်နိုင်အောင်)
    let cameras = []
    try {
      cameras = await Html5Qrcode.getCameras()
    } catch (_) {}
    if (cameras && cameras.length > 0) {
      for (const cam of cameras) {
        try {
          await html5QrCode.start(cam.id, scanConfig, onSuccess, onFail)
          return
        } catch (e) {
          if (html5QrCode) {
            try { if (html5QrCode.isScanning) await html5QrCode.stop() } catch (_) {}
          }
        }
      }
    }

    // 2) Fallback: permissive constraints (မည်သည့်ကင်မရာမဆို)
    const tryConfigs = [
      { facingMode: 'user' },
      { facingMode: 'environment' },
      { video: true },
    ]
    for (const config of tryConfigs) {
      try {
        if (!html5QrCode) html5QrCode = new Html5Qrcode('barcode-scanner-area')
        await html5QrCode.start(config, scanConfig, onSuccess, onFail)
        return
      } catch (e) {
        if (html5QrCode) {
          try { if (html5QrCode.isScanning) await html5QrCode.stop() } catch (_) {}
          html5QrCode = null
        }
      }
    }
    throw new Error('No camera could be started')
  } catch (err) {
    console.warn('Camera start failed:', err)
    showManualInput.value = true
  }
}

const stopScan = () => {
  if (html5QrCode && html5QrCode.isScanning) {
    html5QrCode.stop().catch(() => {})
  }
  emit('close')
}

const handleScanResult = (raw) => {
  let sku = raw.trim()
  try {
    const parsed = JSON.parse(raw)
    if (parsed.sku) sku = String(parsed.sku)
    else if (parsed.SKU) sku = String(parsed.SKU)
  } catch {
    sku = raw.trim()
  }
  if (sku) {
    stopScan()
    emit('scan', sku)
  }
}

const manualInput = () => {
  showManualInput.value = true
}

const submitManual = () => {
  const v = manualValue.value.trim()
  if (v) {
    showManualInput.value = false
    manualValue.value = ''
    emit('close')
    emit('scan', v)
  }
}

watch(
  () => props.show,
  (val) => {
    if (val) {
      showManualInput.value = false
      manualValue.value = ''
      setTimeout(() => startScan(), 300)
    } else {
      stopScan()
    }
  }
)

onUnmounted(() => {
  if (html5QrCode && html5QrCode.isScanning) {
    html5QrCode.stop().catch(() => {})
  }
})
</script>
