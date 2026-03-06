/**
 * Myanmar currency (MMK) - whole numbers only, no decimal points.
 * Use for all price/total/amount display and calculation across POS, Item List, Reports, Receipt.
 */

/**
 * Round to integer (for MMK calculations).
 * @param {number|string|null|undefined} n
 * @returns {number}
 */
export function roundMmk(n) {
  const num = Number(n)
  if (Number.isNaN(num)) return 0
  return Math.round(num)
}

/**
 * Format MMK for display: whole number with locale grouping, no decimals (e.g. 1,500 not 1,500.00).
 * @param {number|string|null|undefined} n
 * @returns {string}
 */
export function formatMmk(n) {
  return roundMmk(n).toLocaleString(undefined, { maximumFractionDigits: 0, minimumFractionDigits: 0 })
}
