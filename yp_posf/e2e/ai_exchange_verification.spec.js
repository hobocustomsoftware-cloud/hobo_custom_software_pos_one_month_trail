// AI + Dollar Exchange + P&L verification
// Verifies: Dashboard (insights, USD rate, today P&L), Settings exchange rate, POS, Accounting P&L
// Run: PLAYWRIGHT_BASE_URL=http://127.0.0.1:5173 npx playwright test e2e/ai_exchange_verification.spec.js --project=chromium
// Optional: TEST_USE_REGISTER=1 to do Register → Setup Wizard first (no pre-existing user needed).
import { test, expect } from '@playwright/test'
import path from 'path'
import fs from 'fs'

const TIMESTAMP = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
const SCREENSHOT_DIR = path.join(process.cwd(), '..', 'demo_results', 'simulation_screenshots', `ai_exchange_${TIMESTAMP}`)
const USE_REGISTER = process.env.TEST_USE_REGISTER === '1' || process.env.TEST_USE_REGISTER === 'true'

async function waitForStable(page, options = {}) {
  const { extraMs = 500 } = options
  await page.waitForLoadState('domcontentloaded')
  await page.waitForTimeout(400)
  const spinner = page.locator('.animate-spin, [role="progressbar"]').first()
  await spinner.waitFor({ state: 'hidden', timeout: 8000 }).catch(() => {})
  await page.waitForTimeout(extraMs)
}

async function ensureLoggedIn(page, screenshotDir) {
  await page.goto('/login')
  await waitForStable(page, { extraMs: 600 })

  if (USE_REGISTER) {
    await page.goto('/register')
    await waitForStable(page)
    const phone = '09' + String(Date.now()).slice(-8)
    const password = 'pass1234'
    const shopName = 'AI Exchange Demo Shop'
    await page.getByPlaceholder(/09|၀၉|phone|email/i).first().fill(phone)
    await page.getByPlaceholder(/my store|ဆိုင်အမည်|shop/i).first().fill(shopName)
    await page.locator('input[type="password"]').first().fill(password)
    await page.locator('input[type="password"]').nth(1).fill(password)
    await page.getByRole('button', { name: /အကောင့်ဖွင့်မည်|create account|register/i }).click()
    await page.waitForTimeout(3000)
    if (page.url().includes('/login')) {
      await page.locator('input[autocomplete="tel email"], input[type="text"]').first().fill(phone)
      await page.getByPlaceholder(/••••••••/).first().fill(password)
      await page.getByRole('button', { name: /ဝင်ရောက်ရန်|sign in/i }).click()
      await page.waitForTimeout(2500)
    }
    await expect(page).toHaveURL(/\/setup-wizard|\//, { timeout: 15000 })
    if (page.url().includes('setup-wizard')) {
      await page.locator('select').first().selectOption({ index: 0 })
      await page.getByRole('button', { name: /complete|ပြီးပါပြီ|go to dashboard/i }).click()
      await page.waitForTimeout(2000)
    }
    return
  }

  const loginId = process.env.TEST_LOGIN_ID || 'owner'
  const password = process.env.TEST_LOGIN_PASSWORD || 'owner123'
  await page.locator('input[autocomplete="tel email"], input[type="text"]').first().fill(loginId)
  await page.getByPlaceholder(/password|••••••••/i).first().fill(password)
  await page.getByRole('button', { name: /ဝင်ရောက်ရန်|sign in|login/i }).click()
  await page.waitForTimeout(2500)
  if (page.url().includes('/login')) {
    await page.screenshot({ path: path.join(screenshotDir, '00_login_failed.png'), fullPage: true })
    throw new Error('Login failed. Set TEST_LOGIN_ID/TEST_LOGIN_PASSWORD or run with TEST_USE_REGISTER=1')
  }
  if (page.url().includes('setup-wizard')) {
    await page.locator('select').first().selectOption({ index: 0 })
    await page.getByRole('button', { name: /complete|ပြီးပါပြီ|go to dashboard/i }).click()
    await page.waitForTimeout(2000)
  }
}

test.describe('AI and Exchange verification', () => {
  test.beforeAll(() => {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true })
    console.log('Screenshots will be saved to:', SCREENSHOT_DIR)
  })

  test('Dashboard: USD rate, P&L, Smart Insight, Business Insights', async ({ page }) => {
    await ensureLoggedIn(page, SCREENSHOT_DIR)

    await page.goto('/')
    await waitForStable(page, { extraMs: 1000 })

    await expect(page.getByText(/USD Rate|MMK per 1 USD|Total Revenue|P&L|ဒီနေ့အရောင်း/i).first()).toBeVisible({ timeout: 15000 })
    await expect(page.getByText(/Smart Business Insight|အကြံပြုချက်|Business Insights|Exchange Rate|Analyzing/i).first()).toBeVisible({ timeout: 15000 })

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '01_dashboard_ai_exchange.png'), fullPage: true })
  })

  test('Settings: Exchange rate modal loads and shows rate', async ({ page }) => {
    await ensureLoggedIn(page, SCREENSHOT_DIR)

    await page.goto('/settings')
    await waitForStable(page, { extraMs: 700 })
    await expect(page.getByText(/ဒေါ်လာဈေးနှုန်း|Exchange Rate|Settings/i).first()).toBeVisible({ timeout: 10000 })

    await page.getByRole('button', { name: /ဒေါ်လာဈေးနှုန်း ချိန်ညှိရန်|exchange rate/i }).click()
    await page.waitForTimeout(800)
    await expect(page.getByText(/ဗဟိုဘဏ်|CBM|ကိုယ်ထိလက်ရောက်|Manual/i).first()).toBeVisible({ timeout: 8000 })
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '02_settings_exchange_modal.png'), fullPage: true })
  })

  test('Accounting P&L page loads', async ({ page }) => {
    await ensureLoggedIn(page, SCREENSHOT_DIR)

    await page.goto('/accounting/pl')
    await waitForStable(page, { extraMs: 700 })
    await expect(page.getByText(/P&L|အမြတ်အစွန်း|ဝင်ငွေ|ကုန်ကျစရိတ်|Profit|Loss/i).first()).toBeVisible({ timeout: 10000 })
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '03_accounting_pl.png'), fullPage: true })
  })

  test('POS: page loads and cart/API areas visible', async ({ page }) => {
    await ensureLoggedIn(page, SCREENSHOT_DIR)

    await page.goto('/sales/pos')
    await waitForStable(page, { extraMs: 1000 })
    await expect(page.getByText(/POS|ရောင်းချရန်|Cart|ခြင်းတောင်း|Search|ရှာပါ/i).first()).toBeVisible({ timeout: 15000 })
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '04_pos.png'), fullPage: true })
  })
})
