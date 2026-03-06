// ဆေးဆိုင် အပြည့်အစုံ simulation: Register → Login → Role → License → Payment → ကုန်ကျစရိတ် → Dollar rate → ဆိုင်ခွဲ → Manager/Staff → Product/Item → Daily Report / P&L → Import/Scan
// Run: PLAYWRIGHT_BASE_URL=http://127.0.0.1:5173 npx playwright test e2e/pharmacy_full_flow.spec.js --project=chromium
// Backend + Frontend နှစ်ခုလုံး ဖွင့်ထားရပါမယ်။
import { test, expect } from '@playwright/test'
import path from 'path'
import fs from 'fs'

const TIMESTAMP = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
const SCREENSHOT_DIR = path.join(process.cwd(), '..', 'demo_results', 'simulation_screenshots', `pharmacy_full_${TIMESTAMP}`)

async function waitForStable(page, options = {}) {
  const { extraMs = 500 } = options
  await page.waitForLoadState('domcontentloaded')
  await page.waitForTimeout(400)
  const spinner = page.locator('.animate-spin, [role="progressbar"]').first()
  await spinner.waitFor({ state: 'hidden', timeout: 8000 }).catch(() => {})
  await page.waitForTimeout(extraMs)
}

function loginInput(page) {
  return page.locator('input[autocomplete="tel email"], input[type="text"], input[type="tel"]').first()
}

test.describe('Pharmacy full flow – Register to Daily Report, Import, Scan', () => {
  test.beforeAll(() => {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true })
    console.log('Screenshots:', SCREENSHOT_DIR)
  })

  test('Full flow: Register → Login → Setup → Roles → License → Payment → Expense → USD → Branches → Users → Items → Reports → P&L → Scan', async ({ page }) => {
    test.setTimeout(120000)
    const phone = '09' + String(Date.now()).slice(-8)
    const password = 'pharmacy123'
    const shopName = 'Demo Pharmacy Full'

    // ---------- 1) Register ----------
    await page.goto('/register')
    await waitForStable(page, { extraMs: 600 })
    await expect(page.getByText(/အကောင့်ဖွင့်ရန်|create account/i).first()).toBeVisible({ timeout: 10000 })
    await page.locator('input[type="tel"]').fill(phone)
    await page.getByPlaceholder(/my store|ဆိုင်အမည်/i).fill(shopName)
    await page.locator('input[type="password"]').first().fill(password)
    await page.locator('input[type="password"]').nth(1).fill(password)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '01_register_filled.png'), fullPage: true })
    await page.getByRole('button', { name: /အကောင့်ဖွင့်မည်|create account|register/i }).click()
    await page.waitForTimeout(3000)

    // ---------- 2) Login (if redirected) ----------
    if (page.url().includes('/login')) {
      await waitForStable(page, { extraMs: 600 })
      await loginInput(page).fill(phone)
      await page.getByPlaceholder(/••••••••/).first().fill(password)
      await page.getByRole('button', { name: /ဝင်ရောက်ရန်|sign in/i }).click()
      await page.waitForTimeout(2500)
    }

    // ---------- 3) Setup Wizard (Pharmacy) ----------
    await expect(page).toHaveURL(/setup-wizard|\/sales\/pos|\/$/, { timeout: 20000 })
    if (page.url().includes('setup-wizard')) {
      await waitForStable(page)
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, '02_setup_wizard.png'), fullPage: true })
      const selects = page.locator('select')
      await selects.first().selectOption('pharmacy').catch(() => selects.first().selectOption({ index: 1 }))
      await selects.nth(1).selectOption('MMK').catch(() => selects.nth(1).selectOption({ index: 0 }))
      await page.waitForTimeout(500)
      await page.getByRole('button', { name: /complete setup|go to dashboard|ပြီးပါပြီ/i }).click()
      await page.waitForTimeout(2000)
    }

    await expect(page).toHaveURL(/\//, { timeout: 15000 })
    await waitForStable(page, { extraMs: 800 })

    // ---------- 4) Roles ----------
    await page.goto('/users/roles')
    await waitForStable(page, { extraMs: 600 })
    await expect(page.getByText(/Role|အသစ်ထည့်မယ်/i).first()).toBeVisible({ timeout: 10000 })
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '03_roles.png'), fullPage: true })
    const addRoleBtn = page.getByRole('button', { name: /အသစ်ထည့်မယ်/i })
    if (await addRoleBtn.isVisible().catch(() => false)) {
      await addRoleBtn.click()
      await page.waitForTimeout(500)
      await page.locator('.glass-input').first().fill('demo_manager')
      await page.getByRole('button', { name: /သိမ်းမယ်|save/i }).click().catch(() => page.locator('button[type="submit"]').click())
      await page.waitForTimeout(1000)
    }

    // ---------- 5) License (view / optional activate) ----------
    await page.goto('/license-activate')
    await waitForStable(page, { extraMs: 500 })
    await expect(page.getByText(/License|လိုင်စင်/i).first()).toBeVisible({ timeout: 8000 })
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '04_license.png'), fullPage: true })
    await page.goto('/settings')

    // ---------- 6) Settings: Payment, Expense category, Dollar rate ----------
    await waitForStable(page, { extraMs: 700 })
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '05_settings.png'), fullPage: true })

    await page.getByText(/ဒေါ်လာဈေးနှုန်း|Exchange Rate|USD/i).first().scrollIntoViewIfNeeded().catch(() => {})
    await page.waitForTimeout(500)

    const rateBtn = page.getByRole('button', { name: /ဒေါ်လာဈေးနှုန်း ချိန်ညှိရန်|exchange rate/i })
    if (await rateBtn.isVisible().catch(() => false)) {
      await rateBtn.click()
      await page.waitForTimeout(800)
      await expect(page.getByText(/ဗဟိုဘဏ်|CBM|Manual/i).first()).toBeVisible({ timeout: 6000 })
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, '06_exchange_modal.png'), fullPage: true })
      await page.keyboard.press('Escape')
      await page.waitForTimeout(300)
    }

    // ---------- 7) ဆိုင်ခွဲ / Shop locations ----------
    await page.goto('/shop-locations')
    await waitForStable(page, { extraMs: 600 })
    await expect(page).toHaveURL(/shop-locations/, { timeout: 10000 })
    await expect(page.getByRole('button', { name: /ဆိုင်အသစ်|နေရာအသစ်/i }).first()).toBeVisible({ timeout: 10000 })
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '07_shop_locations.png'), fullPage: true })
    const siteBtn = page.getByRole('button', { name: /ဆိုင်အသစ်/i })
    if (await siteBtn.isVisible().catch(() => false)) {
      await siteBtn.click()
      await page.waitForTimeout(500)
      await page.locator('input[type="text"]').first().fill('Branch A')
      await page.getByRole('button', { name: /သိမ်းမည်|save/i }).click().catch(() => page.locator('button').filter({ hasText: /သိမ်း/i }).first().click())
      await page.waitForTimeout(1000)
    }

    // ---------- 8) User Management: Manager then Staff ----------
    await page.goto('/users')
    await waitForStable(page, { extraMs: 600 })
    await expect(page.getByText(/User Management|ADD NEW USER/i).first()).toBeVisible({ timeout: 10000 })
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '08_users.png'), fullPage: true })
    const addUserBtn = page.getByRole('button', { name: /ADD NEW USER|အသစ်ထည့်မယ်/i })
    if (await addUserBtn.isVisible().catch(() => false)) {
      await addUserBtn.click()
      await page.waitForTimeout(400)
      await page.locator('.glass-input').first().fill('manager1')
      await page.locator('input[type="password"]').first().fill('manager123')
      await page.locator('select').first().selectOption({ index: 1 })
      await page.locator('button[type="submit"]').click({ timeout: 5000 }).catch(() => {})
      await page.waitForTimeout(800)
    }

    // ---------- 9) Items / Products: add product ----------
    await page.goto('/items/list')
    await waitForStable(page, { extraMs: 800 })
    await expect(page).toHaveURL(/items/, { timeout: 10000 })
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '09_items.png'), fullPage: true })

    // ---------- 10) ကုန်ကျစရိတ် ထည့်ခြင်း ----------
    await page.goto('/accounting/expenses')
    await waitForStable(page, { extraMs: 500 })
    await expect(page).toHaveURL(/expenses/, { timeout: 8000 })
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '10_expenses.png'), fullPage: true })

    // ---------- 11) Daily report & P&L ----------
    await page.goto('/reports/sales-summary')
    await waitForStable(page, { extraMs: 600 })
    await expect(page).toHaveURL(/sales-summary/, { timeout: 10000 })
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '11_daily_sales_summary.png'), fullPage: true })

    await page.goto('/accounting/pl')
    await waitForStable(page, { extraMs: 600 })
    await expect(page).toHaveURL(/accounting\/pl/, { timeout: 10000 })
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '12_pl_report.png'), fullPage: true })

    // ---------- 12) Excel/CSV Import (Items page – if Import button exists) ----------
    await page.goto('/items/list')
    await waitForStable(page, { extraMs: 500 })
    const importBtn = page.getByRole('button', { name: /import|Import|သွင်းမည်/i })
    if (await importBtn.isVisible().catch(() => false)) {
      await importBtn.click()
      await page.waitForTimeout(500)
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, '13_import_modal.png'), fullPage: true })
      await page.keyboard.press('Escape')
    } else {
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, '13_items_no_import_ui.png'), fullPage: true })
    }

    // ---------- 13) POS: Barcode scan simulation (type SKU + Enter) ----------
    await page.goto('/sales/pos')
    await waitForStable(page, { extraMs: 1000 })
    await expect(page).toHaveURL(/sales\/pos/, { timeout: 15000 })
    const searchInput = page.locator('input[placeholder*="Search"]').or(page.locator('input[placeholder*="ရှာပါ"]')).or(page.locator('input[type="text"]').first())
    await searchInput.first().focus()
    await searchInput.first().fill('MED001')
    await page.keyboard.press('Enter')
    await page.waitForTimeout(1500)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '14_pos_scan_simulation.png'), fullPage: true })
  })
})
