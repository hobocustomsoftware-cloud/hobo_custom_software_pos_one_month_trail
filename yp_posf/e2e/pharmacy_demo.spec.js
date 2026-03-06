/**
 * ဆေးဆိုင် Demo – Register ကနေ တစ်လစာ ရောင်းမှတ်တွေ ပြီးရင် Report ထုတ်သည်အထိ
 * Browser ဖွင့်ပြီး လူတစ်ယောက် စမ်းသလို စမ်းမယ်။ Error / layout ပြဿနာရှိရင် report မှာ ပါမယ်။
 *
 * Run (Docker backend + seed_pharmacy_month ပြီးမှ):
 *   PLAYWRIGHT_BASE_URL=http://localhost:8000/app PLAYWRIGHT_HEADED=1 npx playwright test e2e/pharmacy_demo.spec.js --project=chromium
 */
import { test, expect } from '@playwright/test'
import path from 'path'
import fs from 'fs'

const REPORT_DIR = path.join(process.cwd(), '..', 'demo_results', 'pharmacy_demo')
const SLOW_MS = 8000

function attachReport(page, report) {
  if (!report.consoleErrors) report.consoleErrors = []
  if (!report.failedRequests) report.failedRequests = []
  page.on('console', (msg) => {
    if (msg.type() === 'error') report.consoleErrors.push({ text: msg.text(), url: msg.location()?.url })
  })
  page.on('requestfailed', (req) => {
    report.failedRequests.push({ url: req.url().slice(0, 200), failure: req.failure()?.errorText })
  })
}

test.describe('ဆေးဆိုင် Demo – Register → Setup → POS → Reports (တစ်လစာ)', () => {
  test.beforeAll(() => {
    try { fs.mkdirSync(REPORT_DIR, { recursive: true }) } catch (_) {}
  })

  test('Full flow: Register pharmacy → Setup → Dashboard → POS → Sales Summary report', async ({ page }) => {
    const report = {
      startedAt: new Date().toISOString(),
      baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:8000/app',
      steps: [],
      screenshots: [],
      consoleErrors: [],
      failedRequests: [],
      layoutChecks: [],
      stepErrors: [],
    }
    attachReport(page, report)

    const unique = Date.now()
    const registerPhone = `09${String(unique).slice(-8)}`
    const registerEmail = `pharmacy${unique}@demo.local`
    const password = 'demo1234'
    const shopName = 'Demo Pharmacy (ဆေးဆိုင်)'

    const screenshot = async (name) => {
      const file = path.join(REPORT_DIR, `${name}.png`)
      await page.screenshot({ path: file, fullPage: true }).catch(() => {})
      report.screenshots.push({ name, file })
    }

    const step = async (name, fn) => {
      report.steps.push(name)
      const start = Date.now()
      try {
        await fn()
        report.stepTimings = report.stepTimings || []
        report.stepTimings.push({ step: name, ms: Date.now() - start })
        return true
      } catch (e) {
        report.stepTimings = report.stepTimings || []
        report.stepTimings.push({ step: name, ms: Date.now() - start })
        report.stepErrors.push({ step: name, error: e.message })
        throw e
      }
    }

    const waitStable = async (ms = 600) => {
      await page.waitForLoadState('networkidle').catch(() => {})
      await page.waitForTimeout(ms)
      await page.locator('.animate-spin, [role="progressbar"]').first().waitFor({ state: 'hidden', timeout: 5000 }).catch(() => {})
      await page.waitForTimeout(200)
    }

    // --- 1. Register (ဆေးဆိုင်) ---
    await step('1. Open register', async () => {
      await page.goto('/register', { waitUntil: 'domcontentloaded', timeout: 20000 })
      await waitStable(800)
      await screenshot('01_register')
    })

    await step('2. Fill register (pharmacy)', async () => {
      await page.locator('input[type="tel"]').fill(registerPhone).catch(() => {})
      await page.locator('input[type="email"]').fill(registerEmail).catch(() => {})
      const shopInput = page.getByPlaceholder(/my store|ဆိုင်အမည်|shop/i).or(page.locator('input').nth(2))
      await shopInput.fill(shopName)
      await page.locator('input[type="password"]').first().fill(password)
      await page.locator('input[type="password"]').nth(1).fill(password)
      await page.getByRole('button', { name: /create account|အကောင့်ဖွင့်/i }).click()
      await page.waitForTimeout(5000)
      await screenshot('02_after_register')
    })

    const urlAfterReg = page.url()
    if (urlAfterReg.includes('setup-wizard')) {
      report.layoutChecks.push({ where: 'after_register', check: 'redirect to setup-wizard', ok: true })
    } else if (urlAfterReg.includes('login')) {
      report.layoutChecks.push({ where: 'after_register', check: 'redirect to login', ok: true })
    }

    // --- 3. Setup Wizard (pharmacy + MMK) ---
    await step('3. Setup wizard (pharmacy, MMK)', async () => {
      if (!page.url().includes('setup-wizard')) {
        await page.goto('/setup-wizard', { waitUntil: 'domcontentloaded', timeout: 15000 }).catch(() => {})
      }
      await waitStable(600)
      await screenshot('03_setup_wizard')
      await page.locator('select').first().selectOption('pharmacy').catch(() => {})
      await page.locator('select').nth(1).selectOption('MMK').catch(() => {})
      await page.getByRole('button', { name: /complete setup|ပြီးပါပြီ|go to dashboard/i }).click()
      await page.waitForURL(/\/(?!setup-wizard)(\?.*)?$/, { timeout: 20000 }).catch(() => {})
      await waitStable(800)
      await screenshot('04_after_setup')
    })

    report.layoutChecks.push({ where: 'setup', check: 'completed without 403', ok: !(await page.getByText(/403|forbidden/i).first().isVisible().catch(() => false)) })

    // --- 4. Dashboard ---
    await step('4. Dashboard', async () => {
      await page.goto('/')
      await waitStable(800)
      await screenshot('05_dashboard')
      const hasContent = (await page.locator('body').textContent() || '').length > 100
      report.layoutChecks.push({ where: 'dashboard', check: 'body has content', ok: hasContent })
    })

    // --- 5. POS (layout စစ်ဆေး) ---
    await step('5. POS page', async () => {
      await page.goto('/sales/pos')
      await waitStable(1200)
      await screenshot('06_pos')
      const hasCartOrTicket = await page.getByText(/စာရင်း|အရောင်း|ticket|cart/i).first().isVisible().catch(() => false)
      report.layoutChecks.push({ where: 'POS', check: 'cart/ticket area', ok: hasCartOrTicket })
    })

    // Save credentials for second run (after seed_pharmacy_month)
    const credsPath = path.join(REPORT_DIR, 'creds.json')
    fs.writeFileSync(credsPath, JSON.stringify({ phone: registerPhone, password, shopName }), 'utf8')
    report.steps.push('Saved creds for reports run')

    report.finishedAt = new Date().toISOString()

    const reportPath = path.join(REPORT_DIR, 'pharmacy_demo_report.json')
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), 'utf8')
    const txtPath = path.join(REPORT_DIR, 'pharmacy_demo_report.txt')
    const txt = [
      '=== Pharmacy Demo Report ===',
      `Started: ${report.startedAt}`,
      `Base URL: ${report.baseURL}`,
      'Steps: ' + report.steps.join(', '),
      '',
      'Console errors: ' + (report.consoleErrors.length ? report.consoleErrors.map(e => e.text).join('; ') : 'none'),
      'Failed requests: ' + (report.failedRequests.length ? report.failedRequests.length : '0'),
      'Layout checks: ' + report.layoutChecks.map(c => `${c.where}: ${c.check}=${c.ok}`).join(', '),
      '',
      'Screenshots: ' + report.screenshots.map(s => s.name).join(', '),
    ].join('\n')
    fs.writeFileSync(txtPath, txt, 'utf8')
    console.log('\n' + txt)

    if (report.stepErrors?.length) {
      throw new Error('Pharmacy demo had step errors: ' + report.stepErrors.map(e => e.step + ': ' + e.error).join('; '))
    }
  })

  test('Reports after seed: login then Sales Summary (တစ်လစာ စမ်းမယ်)', async ({ page }) => {
    const credsPath = path.join(REPORT_DIR, 'creds.json')
    if (!fs.existsSync(credsPath)) {
      test.skip(true, 'Run the first test (Register → POS) to create creds.json, then run seed_pharmacy_month, then this test.')
      return
    }
    const creds = JSON.parse(fs.readFileSync(credsPath, 'utf8'))
    const report = { startedAt: new Date().toISOString(), screenshots: [], layoutChecks: [], consoleErrors: [], failedRequests: [] }
    attachReport(page, report)

    const screenshot = async (name) => {
      const file = path.join(REPORT_DIR, `${name}.png`)
      await page.screenshot({ path: file, fullPage: true }).catch(() => {})
      report.screenshots.push({ name, file })
    }
    const waitStable = async (ms = 600) => {
      await page.waitForLoadState('networkidle').catch(() => {})
      await page.waitForTimeout(ms)
      await page.locator('.animate-spin').first().waitFor({ state: 'hidden', timeout: 5000 }).catch(() => {})
      await page.waitForTimeout(200)
    }

    await page.goto('/login', { waitUntil: 'domcontentloaded', timeout: 20000 })
    await page.waitForTimeout(800)
    await page.locator('input[type="text"]').first().fill(creds.phone).catch(() => page.getByPlaceholder(/09|phone|ဖုန်း/i).fill(creds.phone))
    await page.getByPlaceholder(/••••••••/).first().fill(creds.password)
    await page.getByRole('button', { name: /sign in|ဝင်ရောက်/i }).click()
    await page.waitForURL(/\/(?!login)(\?.*)?$/, { timeout: 15000 }).catch(() => {})
    await waitStable(800)
    await screenshot('08_after_login')

    await page.goto('/reports/sales-summary')
    await waitStable(1500)
    await screenshot('09_reports_sales_summary')
    const bodyText = await page.locator('body').textContent().then(t => t || '')
    report.layoutChecks.push({ where: 'reports', check: 'page loaded', ok: /report|အစီရင်|sales|summary/i.test(bodyText) })
    report.layoutChecks.push({ where: 'reports', check: 'has content', ok: bodyText.length > 200 })

    report.finishedAt = new Date().toISOString()
    fs.writeFileSync(path.join(REPORT_DIR, 'pharmacy_reports_run.json'), JSON.stringify(report, null, 2), 'utf8')
    console.log('Reports run done. Screenshots:', report.screenshots.map(s => s.name).join(', '))
  })
})
