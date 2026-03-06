/**
 * Reusable thermal receipt printing.
 * - Web/Docker: hidden iframe with 58mm/80mm thermal layout, window.print(), Myanmar font via Google Fonts.
 * - Capacitor: prepares for Bluetooth printer plugin (window.CapacitorPrint or plugin).
 * - MMK: whole numbers only, no decimal points.
 */

const MYANMAR_FONT_URL = 'https://fonts.googleapis.com/css2?family=Noto+Sans+Myanmar:wght@400;500;600;700&display=swap'

function roundMmk(n) {
  const num = Number(n)
  if (Number.isNaN(num)) return 0
  return Math.round(num)
}

function formatMmk(n) {
  return roundMmk(n).toLocaleString(undefined, { maximumFractionDigits: 0, minimumFractionDigits: 0 })
}

function isCapacitor() {
  return typeof window !== 'undefined' && window.Capacitor !== undefined
}

/**
 * Build receipt HTML with Noto Sans Myanmar so thermal/PDF doesn't render boxes.
 * @param {Object} opts - { shopName, invoiceNumber, date, items: [{ name, qty, unitPrice, subtotal }], discount, total, widthMm: 58|80 }
 */
export function buildReceiptHtml(opts) {
  const widthMm = opts.widthMm === 58 ? 58 : 80
  const widthPx = widthMm === 58 ? 220 : 302
  const items = opts.items || []
  const discount = roundMmk(opts.discount || 0)
  const total = roundMmk(opts.total || 0)
  const amountTendered = opts.amountTendered != null ? roundMmk(opts.amountTendered) : null
  const change = opts.change != null ? roundMmk(opts.change) : null
  const shopName = (opts.shopName || 'POS').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  const invoiceNumber = (opts.invoiceNumber || '').replace(/</g, '&lt;')
  const date = opts.date ? new Date(opts.date).toLocaleString('my-MM', { dateStyle: 'short', timeStyle: 'short' }) : new Date().toLocaleString('my-MM', { dateStyle: 'short', timeStyle: 'short' })

  const rows = items
    .map(
      (i) =>
        `<tr>
          <td style="font-size:12px;padding:2px 0;border-bottom:1px dotted #ccc">${(i.name || '').replace(/</g, '&lt;')}</td>
          <td style="text-align:center;font-size:12px">${Number(i.quantity) || 0}</td>
          <td style="text-align:right;font-size:12px">${formatMmk(i.unitPrice)}</td>
          <td style="text-align:right;font-size:12px">${formatMmk(i.subtotal)}</td>
        </tr>`
    )
    .join('')

  return `<!DOCTYPE html>
<html lang="my">
<head>
  <meta charset="UTF-8">
  <title>Receipt</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="${MYANMAR_FONT_URL}" rel="stylesheet">
  <style>
    * { box-sizing: border-box; }
    body {
      font-family: 'Noto Sans Myanmar', 'Inter', sans-serif;
      margin: 0;
      padding: 8px;
      width: ${widthPx}px;
      max-width: ${widthPx}px;
      font-size: 14px;
      line-height: 1.35;
      color: #000;
      background: #fff;
    }
    .receipt-myanmar {
      font-family: 'Noto Sans Myanmar', sans-serif;
    }
    .shop { font-weight: 700; font-size: 16px; margin-bottom: 4px; }
    .meta { font-size: 11px; color: #333; margin-bottom: 8px; }
    table { width: 100%; border-collapse: collapse; font-family: 'Noto Sans Myanmar', 'Inter', sans-serif; }
    th { text-align: left; font-size: 10px; text-transform: uppercase; border-bottom: 1px solid #000; padding: 4px 0; }
    th:nth-child(2), th:nth-child(3), th:nth-child(4) { text-align: right; }
    .total-row { font-weight: 700; font-size: 14px; margin-top: 8px; padding-top: 4px; border-top: 2px solid #000; }
    .thanks { text-align: center; font-size: 12px; margin-top: 12px; }
    @media print {
      body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    }
  </style>
</head>
<body>
  <div class="shop">${shopName}</div>
  <div class="meta">Invoice: ${invoiceNumber}<br>${date}</div>
  <table>
    <thead>
      <tr>
        <th>Item</th>
        <th>Qty</th>
        <th>Price</th>
        <th>Sub</th>
      </tr>
    </thead>
    <tbody>
      ${rows}
    </tbody>
  </table>
  ${discount > 0 ? `<p class="receipt-myanmar" style="margin-top:4px;font-size:14px">လျှော့ဈေး: ${formatMmk(discount)} ကျပ်</p>` : ''}
  <p class="total-row receipt-myanmar">ပေးချေရမည့်ပမာဏ: ${formatMmk(total)} ကျပ်</p>
  ${amountTendered != null ? `<p class="receipt-myanmar" style="font-size:13px">ပေးလိုက်တဲ့ငွေ: ${formatMmk(amountTendered)} ကျပ်</p>` : ''}
  ${change != null ? `<p class="receipt-myanmar" style="font-size:13px;font-weight:700">ပြန်အမ်းရမည့်ငွေ: ${formatMmk(change)} ကျပ်</p>` : ''}
  <p class="thanks receipt-myanmar">ကျေးဇူးတင်ပါသည်</p>
</body>
</html>`
}

let printIframe = null

/**
 * Print receipt: Web = iframe + window.print(); Capacitor = Bluetooth plugin stub.
 * @param {Object} opts - same as buildReceiptHtml + widthMm (58|80)
 */
export function printReceipt(opts) {
  const html = buildReceiptHtml(opts)

  if (isCapacitor()) {
    // Capacitor: Bluetooth thermal printer plugin (e.g. @capacitor-community/bluetooth-le or custom)
    if (typeof window.CapacitorPrint !== 'undefined' && typeof window.CapacitorPrint.print === 'function') {
      window.CapacitorPrint.print(html).catch((err) => {
        console.error('Capacitor print failed:', err)
        fallbackPrint(html, opts.widthMm)
      })
      return
    }
    // Stub: plugin not installed; could open print dialog in WebView as fallback
    fallbackPrint(html, opts.widthMm)
    return
  }

  // Web / Docker: hidden iframe, write HTML, then print
  fallbackPrint(html, opts.widthMm)
}

/**
 * Web/Docker: render receipt in hidden iframe and trigger print dialog (58mm/80mm thermal).
 */
function fallbackPrint(html, widthMm) {
  if (typeof document === 'undefined' || !document.body) return

  const widthPx = widthMm === 58 ? 220 : 302
  if (!printIframe) {
    printIframe = document.createElement('iframe')
    printIframe.setAttribute('style', 'position:absolute;width:1px;height:1px;left:-9999px;top:0;border:0;visibility:hidden')
    printIframe.setAttribute('title', 'Receipt print')
    document.body.appendChild(printIframe)
  }

  const doc = printIframe.contentDocument || printIframe.contentWindow?.document
  if (!doc) return

  doc.open()
  doc.write(html)
  doc.close()

  printIframe.contentWindow.onload = () => {
    try {
      printIframe.contentWindow.focus()
      printIframe.contentWindow.print()
    } catch (e) {
      console.error('Print failed:', e)
    }
  }
}

export function usePrintReceipt() {
  return { printReceipt, buildReceiptHtml, isCapacitor }
}
