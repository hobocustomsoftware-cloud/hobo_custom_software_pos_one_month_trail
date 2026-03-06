/**
 * Loyverse-style product label printing.
 * Label: Item name, Barcode (CODE128 from SKU), Price (MMK), optional SKU.
 * Use for single label (PRINT) or multiple (Create labels with quantity per item).
 */
import JsBarcode from 'jsbarcode'

/** Build one label's HTML (Loyverse style: name, barcode, price, SKU). */
function buildOneLabel(product, options = {}) {
  const showName = options.printName !== false
  const showPrice = options.printPrice !== false
  const showSku = options.printSku !== false
  const barcodeValue = product.sku && String(product.sku).trim() ? product.sku : product.id?.toString() || '0'
  const name = (product.name || '—').slice(0, 36)
  const price = Math.round(Number(product.retail_price) || 0)
  const priceStr = price.toLocaleString(undefined, { maximumFractionDigits: 0 }) + ' MMK'

  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
  try {
    JsBarcode(svg, String(barcodeValue).slice(0, 80), {
      format: 'CODE128',
      width: 1.2,
      height: 44,
      displayValue: false,
      margin: 0,
    })
  } catch (_) {
    svg.innerHTML = '<text x="50%" y="24" text-anchor="middle" font-size="10" fill="#333">No barcode</text>'
  }

  return `
    <div class="loyverse-label">
      ${showName ? `<div class="loyverse-label-name">${escapeHtml(name)}</div>` : ''}
      <div class="loyverse-label-barcode">${svg.outerHTML}</div>
      ${showSku ? `<div class="loyverse-label-sku">${escapeHtml(String(barcodeValue).slice(0, 24))}</div>` : ''}
      ${showPrice ? `<div class="loyverse-label-price">${escapeHtml(priceStr)}</div>` : ''}
    </div>
  `
}

function escapeHtml(text) {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

/** Build full print page HTML with grid of labels (Loyverse-style). */
function getLabelPrintHtml(items, options = {}) {
  const shopName = options.shopName || 'HoBo POS'
  const labelsHtml = items.map(({ product, qty }) => {
    let block = ''
    for (let i = 0; i < qty; i++) block += buildOneLabel(product, options)
    return block
  }).join('')

  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Print Labels - ${shopName}</title>
  <style>
    * { box-sizing: border-box; }
    body { margin: 0; padding: 12px; font-family: system-ui, -apple-system, sans-serif; background: #fff; }
    .loyverse-labels-page { max-width: 100%; }
    .loyverse-labels-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(52mm, 1fr)); gap: 4mm; }
    .loyverse-label {
      width: 52mm; min-height: 32mm; padding: 3mm;
      border: 1px solid #ddd; border-radius: 2px;
      display: flex; flex-direction: column; align-items: center; justify-content: center;
      text-align: center; page-break-inside: avoid;
    }
    .loyverse-label-name { font-size: 11px; font-weight: 700; line-height: 1.2; margin-bottom: 2px; color: #111; }
    .loyverse-label-barcode { margin: 2px 0; }
    .loyverse-label-barcode svg { max-width: 100%; height: auto; max-height: 36px; }
    .loyverse-label-sku { font-size: 9px; color: #555; margin-top: 1px; }
    .loyverse-label-price { font-size: 14px; font-weight: 800; color: #000; margin-top: 2px; }
    @media print {
      body { padding: 0; }
      .loyverse-labels-grid { gap: 2mm; }
      .loyverse-label { border: 1px solid #ccc; }
    }
  </style>
</head>
<body>
  <div class="loyverse-labels-page">
    <div class="loyverse-labels-grid">${labelsHtml}</div>
  </div>
  <script>
    window.onload = function() { window.print(); };
  <\/script>
</body>
</html>`
}

/**
 * Open print window with Loyverse-style labels.
 * @param {Array<{ product: object, qty: number }>} items - product and quantity of labels each
 * @param {object} options - { printName, printPrice, printSku, shopName }
 */
export function printLabels(items, options = {}) {
  const list = items.filter((i) => i.qty > 0 && i.product)
  if (list.length === 0) return
  const html = getLabelPrintHtml(list, options)
  const w = window.open('', '_blank')
  if (!w) return
  w.document.write(html)
  w.document.close()
}

export { buildOneLabel, getLabelPrintHtml }
