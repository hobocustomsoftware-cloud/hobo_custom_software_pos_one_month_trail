/**
 * Browser Demo – အစအဆုံး စမ်းသပ်ချက်
 * - Browser ဖွင့်ပြီး လုပ်ဆောင်ချက်တိုင်းကို မြင်ရမယ် (headed)
 * - Console errors, network failures, loading ကြာချိန် စုစည်း
 * - ခြေလှမ်းတိုင်းမှာ screenshot ယူပြီး နောက်ဆုံး report ထုတ်မယ်
 *
 * Run (browser ပေါ်ပြီး စမ်းမယ်):
 *   npx playwright test e2e/browser_demo_report.spec.js --project=chromium
 *
 * Headed (browser မြင်ရအောင်):
 *   set PLAYWRIGHT_HEADED=1
 *   npx playwright test e2e/browser_demo_report.spec.js --project=chromium
 *
 * Base URL (Django serve /app/ သုံးရင်):
 *   set PLAYWRIGHT_BASE_URL=http://localhost:8000/app
 *   npx playwright test e2e/browser_demo_report.spec.js --project=chromium
 */
import { test, expect } from '@playwright/test'
import path from 'path'
import fs from 'fs'

const REPORT_DIR = path.join(process.cwd(), '..', 'demo_results', 'browser_demo')
const SLOW_THRESHOLD_MS = 5000

/** Collect console messages, failed requests, and step timings */
function attachCollectors(page, report) {
  report.consoleErrors = []
  report.consoleWarnings = []
  report.failedRequests = []
  report.stepTimings = []

  page.on('console', (msg) => {
    const type = msg.type()
    const text = msg.text()
    const loc = msg.location()
    const entry = { type, text, url: loc?.url || '' }
    if (type === 'error') report.consoleErrors.push(entry)
    else if (type === 'warning') report.consoleWarnings.push(entry)
  })

  page.on('requestfailed', (request) => {
    const url = request.url()
    const failure = request.failure()
    report.failedRequests.push({
      url: url.substring(0, 200),
      method: request.method(),
      failure: failure?.errorText || 'unknown',
    })
  })
}

function addStepTiming(report, stepName, ms) {
  report.stepTimings.push({ step: stepName, ms })
  if (ms >= SLOW_THRESHOLD_MS) report.slowSteps = report.slowSteps || []
  if (ms >= SLOW_THRESHOLD_MS) report.slowSteps.push(stepName)
}

async function waitStable(page, ms = 600) {
  await page.waitForLoadState('networkidle').catch(() => {})
  await page.waitForTimeout(ms)
  const spinner = page.locator('.animate-spin, [role="progressbar"]').first()
  await spinner.waitFor({ state: 'hidden', timeout: 4000 }).catch(() => {})
  await page.waitForTimeout(200)
}

test.describe('Browser Demo – အစအဆုံး စမ်းသပ်ချက်', () => {
  test.beforeAll(() => {
    try {
      fs.mkdirSync(REPORT_DIR, { recursive: true })
    } catch (_) {}
  })

  test('Full flow: Login -> Setup Wizard -> Dashboard -> POS -> Settings + errors & timings report', async ({ page }) => {
    const report = {
      startedAt: new Date().toISOString(),
      baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:5173',
      steps: [],
      screenshots: [],
      consoleErrors: [],
      consoleWarnings: [],
      failedRequests: [],
      stepTimings: [],
      slowSteps: [],
      layoutChecks: [],
    }
    attachCollectors(page, report)

    const doRegister = process.env.PLAYWRIGHT_DO_REGISTER === '1' || process.env.PLAYWRIGHT_DO_REGISTER === 'true'
    const loginUser = process.env.PLAYWRIGHT_LOGIN_USER || '09123456789'
    const loginPass = process.env.PLAYWRIGHT_LOGIN_PASS || 'demo1234'
    const uniqueId = Date.now()
    const registerPhone = `09${String(uniqueId).slice(-8)}`
    const registerEmail = `demo${uniqueId}@e2e.local`

    const screenshot = async (name) => {
      const file = path.join(REPORT_DIR, `${name}.png`)
      await page.screenshot({ path: file, fullPage: true }).catch(() => {})
      report.screenshots.push({ name, file })
    }

    const step = async (name, fn) => {
      const start = Date.now()
      report.steps.push(name)
      try {
        await fn()
        const ms = Date.now() - start
        addStepTiming(report, name, ms)
        return true
      } catch (e) {
        addStepTiming(report, name, Date.now() - start)
        report.stepErrors = report.stepErrors || []
        report.stepErrors.push({ step: name, error: e.message })
        throw e
      }
    }

    // --- 0. Optional: Register (first user) then we land on setup-wizard ---
    if (doRegister) {
      await step('0a. Open register', async () => {
        await page.goto('/register', { waitUntil: 'domcontentloaded', timeout: 15000 })
        await waitStable(page, 800)
        await screenshot('00_register_page')
      })
      await step('0b. Fill register and submit', async () => {
        await page.locator('input[type="email"]').fill(registerEmail).catch(() => {})
        await page.locator('input[type="tel"]').fill(registerPhone).catch(() => {})
        await page.getByPlaceholder(/my store|ဆိုင်အမည်|shop/i).fill('E2E Demo Shop').catch(() => page.locator('input').nth(2).fill('E2E Demo Shop'))
        await page.locator('input[type="password"]').first().fill(loginPass)
        await page.locator('input[type="password"]').nth(1).fill(loginPass)
        await page.getByRole('button', { name: /create account|အကောင့်ဖွင့်/i }).click()
        await page.waitForTimeout(4000)
        await screenshot('00_after_register')
      })
      const urlAfterReg = page.url()
      if (urlAfterReg.includes('setup-wizard')) {
        report.layoutChecks.push({ where: 'after register', check: 'redirect to setup-wizard', ok: true })
      } else if (urlAfterReg.includes('login')) {
        report.layoutChecks.push({ where: 'after register', check: 'redirect to login (need login)', ok: true })
      }
    }

    // --- 1. Open Login page (or already on setup-wizard) ---
    await step('1. Open app (login)', async () => {
      if (!doRegister || !page.url().includes('setup-wizard')) {
        await page.goto('/login', { waitUntil: 'domcontentloaded', timeout: 15000 })
        await waitStable(page, 800)
      }
      await screenshot('01_login_page')
      const hasSignIn = await page.getByRole('button', { name: /sign in|ဝင်ရောက်/i }).isVisible().catch(() => false)
      const hasSetup = await page.getByText(/complete setup|ပြီးပါပြီ/i).first().isVisible().catch(() => false)
      expect(hasSignIn || hasSetup, 'Login button or Setup visible').toBeTruthy()
    })

    // --- 2. Login (if on login page) ---
    await step('2. Fill login and submit', async () => {
      if (page.url().includes('login')) {
        const loginInput = page.getByPlaceholder(/email@example|09xxxxxxxx|ဖုန်း|phone/i).or(page.locator('input[type="text"]').first())
        await loginInput.waitFor({ state: 'visible', timeout: 15000 })
        await loginInput.fill(doRegister ? registerPhone : loginUser)
        await page.getByPlaceholder(/••••••••/).first().fill(loginPass)
        await page.getByRole('button', { name: /sign in|ဝင်ရောက်/i }).click()
        await page.waitForTimeout(2000)
      }
      await screenshot('02_after_login_click')
    })

    // --- 3. Expect Setup Wizard or Dashboard ---
    await step('3. After login (setup-wizard or dashboard)', async () => {
      const url = page.url()
      if (url.includes('setup-wizard')) {
        await waitStable(page, 600)
        await screenshot('03_setup_wizard')
        await expect(page.getByText(/setup|business type|complete setup/i).first()).toBeVisible({ timeout: 8000 })
        report.layoutChecks.push({ where: 'setup-wizard', check: 'title or complete button visible', ok: true })
      } else if (url.includes('/') && !url.includes('login')) {
        await waitStable(page, 600)
        await screenshot('03_dashboard')
        report.layoutChecks.push({ where: 'dashboard', check: 'landed after login', ok: true })
      } else {
        const errText = await page.getByText(/invalid|မှား|error|401|403/i).first().textContent().catch(() => '')
        report.layoutChecks.push({ where: 'after login', check: 'redirect', ok: false, note: errText || url })
      }
    })

    // Complete setup wizard if we are on it
    await step('4. Complete setup wizard (if shown)', async () => {
      if (!page.url().includes('setup-wizard')) return
      await page.locator('select').first().selectOption('general').catch(() => {})
      await page.locator('select').nth(1).selectOption('MMK').catch(() => {})
      await page.getByRole('button', { name: /complete setup|ပြီးပါပြီ|go to dashboard/i }).click()
      await page.waitForURL(/\/(?!setup-wizard)(\?.*)?$/, { timeout: 15000 }).catch(() => {})
      await waitStable(page, 800)
      await screenshot('04_after_setup')
    })

    // --- 5. Dashboard ---
    await step('5. Dashboard layout', async () => {
      await page.goto('/')
      await waitStable(page, 800)
      await screenshot('05_dashboard')
      const hasContent = await page.locator('body').textContent().then(t => (t || '').length > 100)
      report.layoutChecks.push({ where: 'dashboard', check: 'body has content', ok: hasContent })
    })

    // --- 6. POS page ---
    await step('6. POS page (layout & products)', async () => {
      await page.goto('/sales/pos')
      await waitStable(page, 1200)
      await screenshot('06_pos_page')
      const hasTicket = await page.getByText(/စာရင်း|အရောင်းဘောက်ချာ|ticket/i).first().isVisible().catch(() => false)
      const hasProducts = await page.locator('.pos-product-card, [class*="pos-product"]').count() > 0 || await page.getByText(/ပစ္စည်း|product/i).first().isVisible().catch(() => false)
      report.layoutChecks.push({ where: 'POS', check: 'ticket or cart area', ok: hasTicket })
      report.layoutChecks.push({ where: 'POS', check: 'product area', ok: hasProducts })
    })

    // --- 6b. Users (staff) – ဝန်ထမ်းစာရင်း ---
    await step('6b. Users (staff) page', async () => {
      await page.goto('/users')
      await waitStable(page, 1000)
      await screenshot('06b_users_staff')
      const hasUsers = await page.getByText(/user|ဝန်ထမ်း|employee|staff/i).first().isVisible().catch(() => false)
      const hasTableOrList = await page.locator('table, [role="table"], .glass-table').count() > 0 || await page.getByRole('button', { name: /add|ထည့်မည်/i }).isVisible().catch(() => false)
      report.layoutChecks.push({ where: 'users (staff)', check: 'users/staff content', ok: hasUsers })
      report.layoutChecks.push({ where: 'users (staff)', check: 'list or add button', ok: hasTableOrList })
    })

    // --- 7. Settings ---
    await step('7. Settings page', async () => {
      await page.goto('/settings')
      await waitStable(page, 800)
      await screenshot('07_settings')
      const hasSettings = await page.getByText(/ချိန်ညှိ|settings|ဆိုင်အမည်/i).first().isVisible().catch(() => false)
      report.layoutChecks.push({ where: 'settings', check: 'settings content', ok: hasSettings })
    })

    // --- 8. Reports (one page) ---
    await step('8. Reports page (sales summary)', async () => {
      await page.goto('/reports/sales-summary')
      await waitStable(page, 1000)
      await screenshot('08_reports_sales_summary')
      const hasReport = await page.locator('body').textContent().then(t => /report|အစီရင်|sales/i.test(t || ''))
      report.layoutChecks.push({ where: 'reports/sales-summary', check: 'page loaded', ok: hasReport })
    })

    report.finishedAt = new Date().toISOString()

    // Write report files
    const reportJson = path.join(REPORT_DIR, 'report.json')
    const reportTxt = path.join(REPORT_DIR, 'report.txt')
    fs.writeFileSync(reportJson, JSON.stringify(report, null, 2), 'utf8')

    const txt = [
      '=== Browser Demo Report ===',
      `Started: ${report.startedAt}`,
      `Base URL: ${report.baseURL}`,
      '',
      '--- Steps ---',
      report.steps.join('\n'),
      '',
      '--- Step timings (ms) ---',
      ...report.stepTimings.map(t => `  ${t.step}: ${t.ms}ms${t.ms >= SLOW_THRESHOLD_MS ? ' (SLOW)' : ''}`),
      '',
      report.slowSteps?.length ? `--- Slow steps (>${SLOW_THRESHOLD_MS}ms) ---\n  ${report.slowSteps.join('\n  ')}` : '',
      '',
      '--- Console errors ---',
      report.consoleErrors.length ? report.consoleErrors.map(e => `  [${e.type}] ${e.text}`).join('\n') : '  (none)',
      '',
      '--- Failed network requests ---',
      report.failedRequests.length ? report.failedRequests.map(f => `  ${f.method} ${f.url} -> ${f.failure}`).join('\n') : '  (none)',
      '',
      '--- Layout checks ---',
      ...report.layoutChecks.map(c => `  ${c.where}: ${c.check} = ${c.ok}${c.note ? ' (' + c.note + ')' : ''}`),
      '',
      '--- Screenshots ---',
      ...report.screenshots.map(s => `  ${s.name} -> ${s.file}`),
    ].filter(Boolean).join('\n')
    fs.writeFileSync(reportTxt, txt, 'utf8')

    console.log('\n' + txt)
    console.log('\nReport saved to:', reportJson, 'and', reportTxt)

    if (report.stepErrors?.length) {
      throw new Error(`Demo had step errors: ${report.stepErrors.map(e => e.step + ': ' + e.error).join('; ')}`)
    }
  })
})
