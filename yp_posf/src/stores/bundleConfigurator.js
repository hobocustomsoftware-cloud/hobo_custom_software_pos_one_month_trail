import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import api from '@/services/api'

/**
 * Bundle configurator store: dynamic pricing (Fixed vs Custom Set),
 * global discount, validation (required components), compatibility tags (warn only).
 */
export const useBundleConfiguratorStore = defineStore('bundleConfigurator', () => {
  const selectedItems = ref([]) // { product, product_id, quantity, unit_price?, tag_names? }
  const bundle = ref(null) // { id, name, bundle_type, pricing_type, bundle_price, discount_type, discount_value, components }
  const compatibilityWarnings = ref([]) // [{ productName, message }]
  const validationResult = ref(null) // { valid, warnings, missing_required }

  const selectedForApi = computed(() =>
    selectedItems.value.map((i) => ({
      product_id: i.product_id ?? i.product?.id,
      quantity: i.quantity ?? 0,
    }))
  )

  /** Unit price for a product (effective_selling_price_mmk or retail_price from API). */
  function getUnitPrice(product) {
    if (!product) return 0
    const n = (v) => (v != null && v !== '' ? Number(v) : 0)
    return n(product.effective_selling_price_mmk) || n(product.retail_price) || 0
  }

  /** Subtotal from selected items: sum(unit_price * qty). */
  const subtotalBeforeDiscount = computed(() => {
    let sum = 0
    for (const item of selectedItems.value) {
      const product = item.product ?? item
      const qty = item.quantity ?? 0
      sum += getUnitPrice(product) * qty
    }
    return sum
  })

  /** If FIXED_BUNDLE and bundle_price set, use that as base; else use subtotal. */
  const subtotal = computed(() => {
    const b = bundle.value
    if (b?.pricing_type === 'FIXED_BUNDLE' && b.bundle_price != null) {
      return Number(b.bundle_price)
    }
    return subtotalBeforeDiscount.value
  })

  /** Global bundle discount (percentage or fixed amount). */
  const discountAmount = computed(() => {
    const b = bundle.value
    if (!b?.discount_type || b.discount_value == null) return 0
    const v = Number(b.discount_value)
    if (b.discount_type === 'PERCENTAGE') {
      return (subtotal.value * v) / 100
    }
    if (b.discount_type === 'FIXED_AMOUNT') return v
    return 0
  })

  /** Final total (subtotal - discount). */
  const total = computed(() => Math.max(0, subtotal.value - discountAmount.value))

  /** Set bundle and optionally reset selected items. */
  function setBundle(b) {
    bundle.value = b
    compatibilityWarnings.value = []
    validationResult.value = null
  }

  /** Add or update product in selection. */
  function setItem(product, quantity) {
    const id = product.id ?? product.product_id
    const idx = selectedItems.value.findIndex((i) => (i.product_id ?? i.product?.id) === id)
    const qty = Math.max(0, Number(quantity) || 0)
    if (qty === 0) {
      if (idx >= 0) selectedItems.value.splice(idx, 1)
      return
    }
    const row = {
      product_id: id,
      product,
      quantity: qty,
      tag_names: product.tag_names ?? product.tags ?? [],
    }
    if (idx >= 0) selectedItems.value[idx] = row
    else selectedItems.value.push(row)
    checkCompatibility(product)
  }

  /** Remove product from selection. */
  function removeItem(productId) {
    selectedItems.value = selectedItems.value.filter(
      (i) => (i.product_id ?? i.product?.id) !== productId
    )
    compatibilityWarnings.value = compatibilityWarnings.value.filter((w) => w.productId !== productId)
  }

  /**
   * Simple compatibility: if bundle has components with product_tag_names,
   * and current selection has products with tags, check for mismatches.
   * Example: bundle expects "Socket-AM4"; user adds a product with "Socket-LGA1700" -> warn.
   * We don't block; we just add to compatibilityWarnings.
   */
  function checkCompatibility(addedProduct) {
    const b = bundle.value
    if (!b?.components?.length) return
    const addedTags = new Set(addedProduct?.tag_names ?? addedProduct?.tags ?? [])
    const addedId = addedProduct?.id ?? addedProduct?.product_id
    for (const comp of b.components) {
      const compTags = comp.product_tag_names ?? comp.product?.tag_names ?? []
      if (compTags.length === 0) continue
      const compSet = new Set(compTags)
      const intersection = [...addedTags].filter((t) => compSet.has(t))
      const hasMismatch = addedTags.size > 0 && compSet.size > 0 && intersection.length === 0
      if (hasMismatch) {
        const existing = compatibilityWarnings.value.find((w) => w.productId === addedId)
        const msg = `Compatibility: "${addedProduct?.name}" may not match expected tags (e.g. ${compTags.join(', ')})`
        if (!existing) {
          compatibilityWarnings.value.push({ productId: addedId, productName: addedProduct?.name, message: msg })
        } else {
          existing.message = msg
        }
        return
      }
    }
    compatibilityWarnings.value = compatibilityWarnings.value.filter((w) => w.productId !== addedId)
  }

  /** Validate bundle (required components) via API. */
  async function validate() {
    const b = bundle.value
    if (!b?.id) {
      validationResult.value = { valid: true, warnings: [], missing_required: [] }
      return validationResult.value
    }
    try {
      // api service က auto token injection လုပ်ပေးတယ်
      const { data } = await api.post(
        'bundles/validate/',
        { bundle_id: b.id, selected_items: selectedForApi.value }
      )
      validationResult.value = data
      return data
    } catch (e) {
      validationResult.value = { valid: false, warnings: [], missing_required: [e?.message || 'Validation request failed'] }
      return validationResult.value
    }
  }

  function clearSelection() {
    selectedItems.value = []
    compatibilityWarnings.value = []
    validationResult.value = null
  }

  return {
    bundle,
    selectedItems,
    selectedForApi,
    compatibilityWarnings,
    validationResult,
    subtotal,
    subtotalBeforeDiscount,
    discountAmount,
    total,
    getUnitPrice,
    setBundle,
    setItem,
    removeItem,
    checkCompatibility,
    validate,
    clearSelection,
  }
})
