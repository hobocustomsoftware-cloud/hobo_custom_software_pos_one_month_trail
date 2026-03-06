/**
 * Business Cycle Test – Final validation before Cloud deployment.
 * Steps: A) Register (Phone) + Setup Wizard (Pharmacy/MMK), B) Items page, C) POS, D) Sales Summary.
 * Collects 404/401/403/500 from responses and writes pre_deployment_report data.
 *
 * Run (Docker up first):
 *   cd yp_posf && PLAYWRIGHT_BASE_URL=http://localhost/app npx playwright test e2e/business_cycle.spec.js --project=chromium
 * Headed (show browser):
 *   PLAYWRIGHT_BASE_URL=http://localhost/app npx playwright test e2e/business_cycle.spec.js --project=chromium --headed
 */
const { test, expect } = require('@playwright/test')
const path = require('path')
const fs = require('fs')

const BASE = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost/app'
const REPORT_PATH = path.join(process.cwd(), '..', 'pre_deployment_report.md')

function collectApiErrors(page, report) {
  report.apiErrors = report.apiErrors || []
  page.on('response', (r) => {
    const status = r.status()
    const url = r.url()
    if ((status === 401 || status === 403 || status === 500) && url.includes('/api/')) {
      report.apiErrors.push({ status, url: url.replace(/^.*\/api/, '/api').slice(0, 120) })
    }
  })
}

function collect404Assets(page, report) {
  report.asset404 = report.asset404 || []
  page.on('response', (r) => {
    if (r.status() === 404 && (r.url().includes('/assets/') || /\.(js|css)$/.test(r.url()))) {
      report.asset404.push(r.url().slice(-80))
    }
  })
}

test.describe('Business Cycle – Pre-Deployment', () => {
  test('Step A–E: Register (Phone) → Setup Wizard → Items → POS → Sales Summary + Error audit', async ({ page }) => {
    test.setTimeout(120000)
    const report = {
      runAt: new Date().toISOString(),
      baseURL: BASE,
      steps: {},
      apiErrors: [],
      asset404: [],
      consoleErrors: [],
    }
    collectApiErrors(page, report)
    collect404Assets(page, report)
    page.on('console', (msg) => {
      if (msg.type() === 'error') report.consoleErrors.push(msg.text().slice(0, 200))
    })

    const waitStable = async (ms = 600) => {
      await page.waitForLoadState('networkidle').catch(() => {})
      await page.waitForTimeout(ms)
    }

    const phone = '09' + String(Date.now()).slice(-8)
    const password = 'Demo123!'

    // --- Step A: Register via Phone + Setup Wizard (Pharmacy / MMK) ---
    await page.goto(`${BASE}/register`, { waitUntil: 'networkidle', timeout: 30000 })
    await waitStable(800)
    await page.locator('input[type="tel"]').fill(phone)
    await page.getByPlaceholder(/my store|ဆိုင်အမည်|shop/i).fill('QA Pharmacy')
    await page.locator('input[type="password"]').first().fill(password)
    await page.locator('input[type="password"]').nth(1).fill(password)
    await page.getByRole('button', { name: /create account|အကောင့်ဖွင့်/i }).click()
    await page.waitForURL(/\/(setup-wizard|app\/setup-wizard)/, { timeout: 20000 }).catch(() => {})
    await waitStable(600)
    report.steps.A_Register = page.url().includes('setup-wizard') ? 'OK' : 'Check redirect'

    if (page.url().includes('setup-wizard')) {
      await page.locator('select').first().selectOption(/pharmacy/).catch(() => {})
      await page.locator('select').nth(1).selectOption('MMK').catch(() => {})
      await page.getByRole('button', { name: /complete setup|ပြီးပါပြီ|go to dashboard/i }).click()
      await page.waitForURL(/\/(?!setup-wizard)(\?.*)?$/, { timeout: 15000 }).catch(() => {})
      await waitStable(800)
    }
    report.steps.A_SetupWizard = !page.url().includes('setup-wizard') ? 'OK' : 'Still on wizard'

    // --- Step B: Items (Item List) ---
    await page.goto(`${BASE}/products`, { waitUntil: 'networkidle', timeout: 15000 })
    await waitStable(1000)
    const itemsBody = await page.locator('body').textContent().then(t => t || '')
    report.steps.B_Items = /item|product|ပစ္စည်း|category/i.test(itemsBody) ? 'OK' : 'Check page'

    // --- Step C/D: POS ---
    await page.goto(`${BASE}/sales/pos`, { waitUntil: 'networkidle', timeout: 15000 })
    await waitStable(1000)
    const posBody = await page.locator('body').textContent().then(t => t || '')
    report.steps.C_POS = /cart|pos|စာရင်း|sale/i.test(posBody) ? 'OK' : 'Check page'

    // --- Step E: Sales Summary ---
    await page.goto(`${BASE}/reports/sales-summary`, { waitUntil: 'networkidle', timeout: 15000 })
    await waitStable(1500)
    const reportBody = await page.locator('body').textContent().then(t => t || '')
    report.steps.E_SalesSummary = /sales|summary|အစီရင်|report/i.test(reportBody) ? 'OK' : 'Check page'

    // --- Assert: No 404 on assets ---
    expect(report.asset404.length).toBe(0)

    // --- Write report snippet for pre_deployment_report.md ---
    const snippet = [
      '## Business Cycle E2E (automated)',
      `Run: \`${report.runAt}\``,
      `Base: \`${report.baseURL}\``,
      '',
      '| Step | Result |',
      '|------|--------|',
      Object.entries(report.steps).map(([k, v]) => `| ${k} | ${v} |`).join('\n'),
      '',
      '| Check | Count |',
      '|-------|-------|',
      `| Asset 404s | ${report.asset404.length} |`,
      `| API 401/403/500 | ${report.apiErrors.length} |`,
      '',
      report.apiErrors.length ? '**API errors:** ' + report.apiErrors.slice(0, 10).map(e => `${e.status} ${e.url}`).join('; ') : '',
    ].filter(Boolean).join('\n')

    try {
      let existing = ''
      if (fs.existsSync(REPORT_PATH)) {
        existing = fs.readFileSync(REPORT_PATH, 'utf8')
        const marker = '## Business Cycle E2E (automated)'
        const idx = existing.indexOf(marker)
        if (idx >= 0) {
          const end = existing.indexOf('\n## ', idx + 5)
          existing = existing.slice(0, idx) + (end > idx ? existing.slice(end) : '')
        }
      }
      const sep = existing && !existing.endsWith('\n') ? '\n\n' : ''
      fs.writeFileSync(REPORT_PATH, existing + sep + snippet + '\n', 'utf8')
    } catch (_) {}

    if (report.stepErrors?.length) throw new Error(report.stepErrors.map(e => e.step + ': ' + e.error).join('; '))
  })
})
