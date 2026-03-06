// Pharmacy simulation (Vite dev UI): Register (phone+shop) → Setup Wizard (pharmacy) → POS → Daily Report screenshots
// Run:
//   PLAYWRIGHT_BASE_URL=http://127.0.0.1:5173 npx playwright test e2e/pharmacy_simulation.spec.js --project=chromium
import { test, expect } from '@playwright/test'
import path from 'path'
import fs from 'fs'

const TIMESTAMP = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
const SCREENSHOT_DIR = path.join(process.cwd(), '..', 'demo_results', 'simulation_screenshots', `pharmacy_${TIMESTAMP}`)

async function waitForStable(page, options = {}) {
  const { extraMs = 500 } = options
  // Don't rely on networkidle: app may poll (notifications/sync) and never become idle.
  await page.waitForLoadState('domcontentloaded')
  await page.evaluate(() => document.fonts && document.fonts.ready).catch(() => {})
  await page.waitForTimeout(400)
  const spinner = page.locator('.animate-spin, [role="progressbar"]').first()
  await spinner.waitFor({ state: 'hidden', timeout: 6000 }).catch(() => {})
  await page.waitForTimeout(extraMs)
}

const PAGES = [
  { path: '/', name: '01_dashboard' },
  { path: '/sales/pos', name: '02_pos' },
  { path: '/sales/history', name: '03_sales_history' },
  { path: '/reports/sales-summary', name: '04_daily_sales_summary' },
  { path: '/reports/sales-by-payment', name: '05_sales_by_payment' },
  { path: '/items/list', name: '06_items_list' },
  { path: '/inventory', name: '07_inventory' },
  { path: '/service', name: '08_service' },
  { path: '/settings', name: '09_settings' },
]

test.describe('Pharmacy simulation – Register to Daily Report (Vite)', () => {
  test.beforeAll(() => {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true })
    console.log('Screenshots will be saved to:', SCREENSHOT_DIR)
  })

  test('Register → Setup Wizard (Pharmacy) → feature pages (screenshots)', async ({ page }) => {
    const phone = '09' + String(Date.now()).slice(-8)
    const password = 'pharmacy123'
    const shopName = 'Demo Pharmacy Shop'

    // 1) Login page
    await page.goto('/login')
    await waitForStable(page, { extraMs: 700 })
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '00_login.png'), fullPage: true })

    // 2) Register (phone + shop name)
    await page.goto('/register')
    await waitForStable(page)
    await expect(page.getByText(/အကောင့်ဖွင့်ရန်|create account/i).first()).toBeVisible({ timeout: 10000 })
    await page.getByPlaceholder(/09xxxxxxxx|\+959|၀၉/i).fill(phone)
    await page.getByPlaceholder(/my store|ဆိုင်အမည်/i).fill(shopName)
    await page.locator('input[type="password"]').first().fill(password)
    await page.locator('input[type="password"]').nth(1).fill(password)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '00_register_filled.png'), fullPage: true })
    await page.getByRole('button', { name: /အကောင့်ဖွင့်မည်|create account|register/i }).click()
    await page.waitForTimeout(2500)

    // Some flows redirect to /login after successful registration (no auto-login)
    if (page.url().includes('/login')) {
      await waitForStable(page, { extraMs: 600 })
      await page.locator('input[autocomplete="tel email"], input[type="text"], input[type="tel"]').first().fill(phone)
      await page.getByPlaceholder(/••••••••/).first().fill(password)
      await page.getByRole('button', { name: /ဝင်ရောက်ရန်|sign in/i }).click()
      await page.waitForTimeout(2000)
    }

    // 3) Setup Wizard
    await expect(page).toHaveURL(/\/setup-wizard/, { timeout: 20000 })
    await waitForStable(page)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '00_setup_wizard.png'), fullPage: true })
    const selects = page.locator('select')
    await selects.first().selectOption('pharmacy')
    await selects.nth(1).selectOption('MMK')
    await page.waitForTimeout(500)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '00_setup_wizard_pharmacy_mmk.png'), fullPage: true })
    await page.getByRole('button', { name: /complete setup|go to dashboard|ပြီးပါပြီ/i }).click()

    // 4) Pages + daily report
    await expect(page).toHaveURL(/\//, { timeout: 15000 })
    await waitForStable(page, { extraMs: 800 })
    for (const p of PAGES) {
      await page.goto(p.path)
      await waitForStable(page, { extraMs: 700 })
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${p.name}.png`), fullPage: true })
    }
    await page.goto('/reports/sales-summary')
    await waitForStable(page)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '10_daily_report_sales_summary.png'), fullPage: true })
  })
})

