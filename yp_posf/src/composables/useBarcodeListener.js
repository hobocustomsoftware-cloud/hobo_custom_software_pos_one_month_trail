/**
 * Global barcode listener for USB scanner (keyboard wedge).
 * Buffers keydown; on Enter with non-empty buffer, emits barcode and clears.
 * Clears buffer after idle (100ms) so slow typing isn't treated as a scan.
 * Ignores input when focus is in text input/textarea so normal typing isn't captured.
 */

const IDLE_MS = 100
const INPUT_SELECTOR = 'input, textarea, [contenteditable="true"]'

let buffer = ''
let idleTimer = null
let listenerAttached = false
let callback = null

function clearBuffer() {
  buffer = ''
  if (idleTimer) {
    clearTimeout(idleTimer)
    idleTimer = null
  }
}

function flushBarcode() {
  const barcode = buffer.trim()
  clearBuffer()
  if (barcode && typeof callback === 'function') {
    callback(barcode)
  }
}

function isFocusedOnInput() {
  if (typeof document === 'undefined' || !document.activeElement) return false
  const el = document.activeElement
  return el.matches && el.matches(INPUT_SELECTOR)
}

function onKeyDown(ev) {
  // Ignore when user is typing in an input/textarea
  if (isFocusedOnInput()) return

  if (ev.key === 'Enter') {
    ev.preventDefault()
    flushBarcode()
    return
  }

  // Only append printable single characters (scanners typically send ASCII)
  if (ev.key && ev.key.length === 1 && !ev.ctrlKey && !ev.metaKey && !ev.altKey) {
    buffer += ev.key
    if (idleTimer) clearTimeout(idleTimer)
    idleTimer = setTimeout(clearBuffer, IDLE_MS)
  }
}

/**
 * Start listening for barcode input (USB scanner as keyboard).
 * @param {Function} onBarcode - (barcode: string) => void; e.g. search product and add to cart
 */
export function startBarcodeListener(onBarcode) {
  callback = onBarcode
  if (listenerAttached) return
  if (typeof document === 'undefined') return
  document.addEventListener('keydown', onKeyDown, true)
  listenerAttached = true
}

/**
 * Stop listening and clear buffer.
 */
export function stopBarcodeListener() {
  if (typeof document === 'undefined') return
  document.removeEventListener('keydown', onKeyDown, true)
  listenerAttached = false
  clearBuffer()
  callback = null
}

export function useBarcodeListener() {
  return { startBarcodeListener, stopBarcodeListener }
}
