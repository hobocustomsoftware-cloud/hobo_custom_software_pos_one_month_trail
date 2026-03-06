// 1-Month Business Simulation Test – QA Automation & Performance
// Run order: 1) Backend + frontend up, 2) Run this spec (Phase 1). 3) Run backend: simulation_1month_data. 4) Run Phase 3–4 (reports).
// Run: scripts/run_1month_simulation.bat (or .sh) for full flow.
//      PLAYWRIGHT_BASE_URL=http://localhost:80 npx playwright test e2e/one_month_simulation.spec.js --project=chromium [--headed]
// Screenshots: demo_results/one_month_simulation/  |  performance_audit.md in demo_results/
import { test, expect } from '@playwright/test'
import path from 'path'
import fs from 'fs'

const SCREENSHOT_DIR = path.join(process.cwd(), '..', 'demo_results', 'one_month_simulation')
const PERF_FILE = path.join(process.cwd(), '..', 'demo_results', 'performance_audit.md')

function ms(ms) { return new Promise(r => setTimeout(r, ms)) }

async function waitStable(page, msWait = 600) {
  await page.waitForLoadState('networkidle')
  await ms(msWait)
}

test.describe('1-Month Business Simulation Test', () => {
  test.beforeAll(() => {
    try { fs.mkdirSync(SCREENSHOT_DIR, { recursive: true }) } catch (_) {}
  })

  // ---------- Show Owner Registration (Fix backend first, then START browser – user sees this) ----------
  test('00 – Open Owner Registration page', async ({ page }) => {
    await page.goto('/register', { waitUntil: 'networkidle', timeout: 30000 })
    await ms(1500)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '00_owner_registration.png'), fullPage: true })
    await expect(page.locator('#app')).toBeVisible()
    await expect(page).toHaveURL(/\/register/)
  })

  // ---------- Phase 1: Registration & Setup (Owner Role) ----------
  test('Phase 1a – Owner Registration', async ({ page }) => {
    test.setTimeout(60000)
    await page.goto('/register', { waitUntil: 'networkidle', timeout: 30000 })
    await ms(1500)
    const email = `owner.sim.${Date.now()}@test.local`
    const password = 'OwnerSim123!'
    await page.locator('input[type="email"]').first().fill(email)
    await page.locator('input[type="text"]').first().fill('Pharmacy Simulation Shop')
    await page.locator('input[type="password"]').first().fill(password)
    await page.locator('input[type="password"]').nth(1).fill(password)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '01_owner_register.png'), fullPage: true })
    await page.getByRole('button', { name: /create account|စာရင်းသွင်း/i }).click()
    await expect(page).toHaveURL(/\/setup-wizard/, { timeout: 20000 })
  })

  test('Phase 1b – Setup Wizard Pharmacy, seed units', async ({ page }) => {
    test.setTimeout(45000)
    await page.goto('/setup-wizard', { waitUntil: 'networkidle', timeout: 30000 })
    await ms(1000)
    await page.locator('select').first().selectOption('pharmacy')
    await page.locator('select').nth(1).selectOption('MMK')
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '02_setup_wizard_pharmacy.png'), fullPage: true })
    await page.getByRole('button', { name: /complete setup|go to dashboard/i }).click()
    await expect(page).toHaveURL(/\//, { timeout: 15000 })
    await waitStable(page, 1000)
  })

  test('Phase 1c – Create 4 roles: Manager, Inventory_Staff, Sale_Staff, Cashier', async ({ page }) => {
    test.setTimeout(60000)
    await page.goto('/users/roles', { waitUntil: 'networkidle', timeout: 30000 })
    await waitStable(page, 800)
    const roles = ['Manager', 'Inventory_Staff', 'Sale_Staff', 'Cashier']
    for (const name of roles) {
      const row = page.locator('table tbody tr').filter({ has: page.getByText(name) })
      if (await row.count() === 0) {
        await page.getByRole('button', { name: /add|ထည့်မယ်|အသစ်/i }).first().click()
        await ms(500)
        await page.locator('input[type="text"]').last().fill(name)
        await page.getByRole('button', { name: /save|သိမ်းမယ်/i }).click()
        await ms(800)
      }
    }
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '03_roles_created.png'), fullPage: true })
  })

  // ---------- Phase 3 & 4: Reports load time + screenshot (run AFTER simulation_1month_data) ----------
  test('Phase 3–4 – Sales Summary & Sale by Item load time + report_load_1month.png', async ({ page }) => {
    test.setTimeout(90000)
    const loginEmail = process.env.PLAYWRIGHT_LOGIN_EMAIL || process.env.PLAYWRIGHT_VERIFY_EMAIL
    const loginPassword = process.env.PLAYWRIGHT_LOGIN_PASSWORD || process.env.PLAYWRIGHT_VERIFY_PASSWORD
    await page.goto('/', { waitUntil: 'networkidle' })
    await ms(800)
    const onLogin = await page.locator('input[type="email"], input[name="email"], input[type="text"]').first().isVisible().catch(() => false)
    if (onLogin && loginEmail && loginPassword) {
      await page.locator('input[type="email"], input[name="email"]').first().fill(loginEmail)
      await page.locator('input[type="password"]').first().fill(loginPassword)
      await page.getByRole('button', { name: /sign in|login|အကောင့်ဝင်/i }).click()
      await expect(page).toHaveURL(/\/(setup-wizard)?(\?.*)?$/, { timeout: 15000 }).catch(() => {})
      await page.goto('/', { waitUntil: 'networkidle' })
    } else if (onLogin) {
      test.skip(true, 'Set PLAYWRIGHT_LOGIN_EMAIL and PLAYWRIGHT_LOGIN_PASSWORD after Phase 1 to run reports test')
      return
    }
    await page.goto('/reports/sales-summary', { waitUntil: 'networkidle', timeout: 60000 })
    const t0 = Date.now()
    await page.waitForSelector('table, .chart, [class*="chart"], [class*="report"]', { timeout: 25000 }).catch(() => {})
    const salesSummaryLoadMs = Date.now() - t0
    await waitStable(page, 500)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '04_sales_summary_loaded.png'), fullPage: true })

    await page.goto('/reports/sale-by-item', { waitUntil: 'networkidle', timeout: 60000 })
    const t1 = Date.now()
    await page.waitForSelector('table, .chart, [class*="chart"], [class*="report"]', { timeout: 25000 }).catch(() => {})
    const saleByItemLoadMs = Date.now() - t1
    await waitStable(page, 500)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '05_sale_by_item_loaded.png'), fullPage: true })

    // Single combined screenshot for "report_load_1month.png"
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'report_load_1month.png'), fullPage: true })

    // Append load times to performance_audit.md (docker stats added by run script)
    const auditDir = path.dirname(PERF_FILE)
    try { fs.mkdirSync(auditDir, { recursive: true }) } catch (_) {}
    const loadTimes = `
## 1-Month Simulation – Report load times
- Sales Summary: ${(salesSummaryLoadMs / 1000).toFixed(2)} s
- Sale by Item: ${(saleByItemLoadMs / 1000).toFixed(2)} s
- Captured: ${new Date().toISOString()}
`
    try {
      fs.appendFileSync(PERF_FILE, loadTimes)
    } catch (_) {}
  })
})
