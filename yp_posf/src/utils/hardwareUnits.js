/**
 * Hardware mode units and conversion factors for UnitSelectorModal and POS cart.
 * Base unit for count-based: Piece. Price is per base unit; line total = basePrice * quantity * factor.
 * Length units (Feet, Meter, Peittha): factor 1 (quantity is in that unit; price per unit).
 */

export const HARDWARE_UNITS = [
  { value: 'piece', label: 'ခု (Piece)', labelEn: 'Piece', factor: 1 },
  { value: 'dozen', label: 'ဒါဇင် (Dozen)', labelEn: 'Dozen', factor: 12 },
  { value: 'box', label: 'ဖာ (Box)', labelEn: 'Box', factor: 12 },
  { value: 'feet', label: 'ပေ (Feet)', labelEn: 'Feet', factor: 1 },
  { value: 'meter', label: 'မီတာ (Meter)', labelEn: 'Meter', factor: 1 },
  { value: 'peittha', label: 'ပိတ်သာ (Peittha)', labelEn: 'Peittha', factor: 1 },
]

const factorMap = Object.fromEntries(HARDWARE_UNITS.map((u) => [u.value, u.factor]))
const labelMap = Object.fromEntries(HARDWARE_UNITS.map((u) => [u.value, u.label]))

/**
 * Conversion factor to base (piece for count; 1 for length).
 * Used to compute: unitPrice = basePrice * factor, lineTotal = unitPrice * quantity.
 */
export function getConversionFactor(unit) {
  if (!unit) return 1
  return factorMap[unit] ?? 1
}

export function getUnitLabel(unit) {
  return labelMap[unit] || unit
}

/** Pharmacy POS: လုံး / တစ်ကတ် / ဗူး / ပုလင်း */
const pharmacyLabelMap = {
  piece: 'လုံး',
  strip: 'တစ်ကတ်',
  box: 'ဗူး',
  bottle: 'ပုလင်း',
}
export function getPharmacyUnitLabel(unit) {
  return pharmacyLabelMap[unit] || unit
}
