<script setup>
import { onMounted, watch, ref } from 'vue'
import JsBarcode from 'jsbarcode'

const props = defineProps(['value'])
const barcodeRef = ref(null)

const generateBarcode = () => {
  if (props.value) {
    JsBarcode(barcodeRef.value, props.value, {
      format: 'CODE128',
      width: 1.5,
      height: 40,
      displayValue: false, // Table ထဲမှာဆိုတော့ စာသားမပါဘဲ Barcode သီးသန့်ပဲပြတာ ပိုလှပါတယ်
      margin: 0,
    })
  }
}

onMounted(generateBarcode)
watch(() => props.value, generateBarcode)
</script>

<template>
  <svg ref="barcodeRef"></svg>
</template>
