// Full simulation: Register → Setup Wizard → ဆိုင်စတင် → feature list အဆင့်ဆင့် → daily report
// Screenshots saved to: demo_results/simulation_screenshots/YYYY-MM-DD_HH-MM-SS/
// Run: PLAYWRIGHT_BASE_URL=http://127.0.0.1:5173 npx playwright test e2e/full_simulation_spec.js --project=chromium
// Requires: Backend (8000) + Frontend (5173) running
import { test, expect } from '@playwright/test'
import path from 'path'
import fs from 'fs'

const TIMESTAMP = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
const SCREENSHOT_DIR = path.join(process.cwd(), '..', 'demo_results', 'simulation_screenshots', TIMESTAMP)

async function waitForStable(page, options = {}) {
  const { extraMs = 500 } = options
  await page.waitForLoadState('networkidle')
  await page.evaluate(() => document.fonts && document.fonts.ready).catch(() => {})
  await page.waitForTimeout(400)
  const spinner = page.locator('.animate-spin, [role="progressbar"]').first()
  await spinner.waitFor({ state: 'hidden', timeout: 6000 }).catch(() => {})
  await page.waitForTimeout(extraMs)
}

const FEATURE_PAGES = [
  { path: '/', name: '01_dashboard' },
  { path: '/sales/pos', name: '02_pos' },
  { path: '/sales/history', name: '03_sales_history' },
  { path: '/sales/approve', name: '04_approve' },
  { path: '/reports/sales-summary', name: '05_daily_sales_summary' },
  { path: '/reports/sales', name: '06_reports_sales' },
  { path: '/reports/sale-by-item', name: '07_reports_sale_by_item' },
  { path: '/reports/sales-by-category', name: '08_reports_sales_by_category' },
  { path: '/reports/sales-by-employee', name: '09_reports_sales_by_employee' },
  { path: '/reports/sales-by-payment', name: '10_reports_sales_by_payment' },
  { path: '/reports/receipts', name: '11_reports_receipts' },
  { path: '/reports/discount', name: '12_reports_discount' },
  { path: '/reports/shift', name: '13_reports_shift' },
  { path: '/reports/inventory', name: '14_reports_inventory' },
  { path: '/reports/service', name: '15_reports_service' },
  { path: '/reports/customers', name: '16_reports_customers' },
  { path: '/inventory', name: '17_inventory' },
  { path: '/items/list', name: '18_items_list' },
  { path: '/items/categories', name: '19_items_categories' },
  { path: '/inventory/history', name: '20_inventory_history' },
  { path: '/service', name: '21_service' },
  { path: '/users', name: '22_users' },
  { path: '/accounting/expenses', name: '23_accounting_expenses' },
  { path: '/accounting/pl', name: '24_accounting_pl' },
  { path: '/settings', name: '25_settings' },
]

test.describe('Full simulation – Register to Daily Report', () => {
  test.beforeAll(() => {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true })
    console.log('Screenshots will be saved to:', SCREENSHOT_DIR)
  })

  test('Register → Setup Wizard → ဆိုင်စတင် → feature list → daily report (screenshots)', async ({ page }) => {
    const phone = '09' + String(Date.now()).slice(-8)
    const password = 'SimPass123!'
    const shopName = 'Simulation Demo Shop'

    // ---- 1) Login page ----
    await page.goto('/login')
    await waitForStable(page, { extraMs: 600 })
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '00_login.png'), fullPage: true })

    // ---- 2) Register ----
    await page.goto('/register')
    await waitForStable(page)
    await expect(page.getByRole('heading', { name: /စာရင်းသွင်းရန်|create account|register/i })).toBeVisible({ timeout: 10000 })
    await page.getByLabel(/ဖုန်းနံပါတ်|phone number/i).fill(phone)
    await page.getByLabel(/ဆိုင်အမည်|shop name/i).fill(shopName)
    await page.locator('input[type="password"]').first().fill(password)
    await page.locator('input[type="password"]').nth(1).fill(password)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '00_register_filled.png'), fullPage: true })
    await page.getByRole('button', { name: /စာရင်းသွင်းရန်|register|create account/i }).click()
    await page.waitForTimeout(4000)
    if (page.url().includes('/register')) {
      const err = await page.getByText(/already exists|duplicate|taken|မရပါ/i).isVisible().catch(() => false)
      if (err) {
        await page.getByLabel(/ဖုန်းနံပါတ်/i).fill('09' + String(Date.now()).slice(-8))
        await page.getByRole('button', { name: /စာရင်းသွင်းရန်|register|create account/i }).click()
        await page.waitForTimeout(4000)
      }
    }

    await expect(page).toHaveURL(/\/setup-wizard/, { timeout: 20000 })

    // ---- 3) Setup Wizard ----
    await waitForStable(page)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '00_setup_wizard.png'), fullPage: true })
    // Select Pharmacy + MMK for the first run (user requested pharmacy first)
    const selects = page.locator('select')
    await selects.first().selectOption('pharmacy')
    await selects.nth(1).selectOption('MMK')
    await page.waitForTimeout(500)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '00_setup_wizard_pharmacy_mmk.png'), fullPage: true })
    await page.getByRole('button', { name: /complete setup|go to dashboard|ပြီးပါပြီ/i }).click()
    await expect(page).toHaveURL(/\/(\?.*)?$/, { timeout: 15000 })
    await waitForStable(page, { extraMs: 800 })

    // ---- 4) Feature list + Daily report (screenshots) ----
    for (const { path: routePath, name } of FEATURE_PAGES) {
      await page.goto(routePath)
      await waitForStable(page, { extraMs: 600 })
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${name}.png`), fullPage: true })
    }

    // ---- 5) Daily report (sales summary) again as "daily report" ----
    await page.goto('/reports/sales-summary')
    await waitForStable(page)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '26_daily_report_sales_summary.png'), fullPage: true })

    console.log('All screenshots saved to:', SCREENSHOT_DIR)
  })
})
