// Backend–Frontend connection + Register → role-based flow verification
// Run: PLAYWRIGHT_BASE_URL=http://localhost:80 npx playwright test e2e/backend_frontend_verification.spec.js --project=chromium
// Screenshots: demo_results/backend_frontend_verification/
import { test, expect } from '@playwright/test'
import path from 'path'
import fs from 'fs'

const SCREENSHOT_DIR = path.join(process.cwd(), '..', 'demo_results', 'backend_frontend_verification')

async function waitStable(page, ms = 500) {
  await page.waitForLoadState('networkidle')
  await page.waitForTimeout(ms)
}

test.describe('Backend–Frontend verification', () => {
  test.beforeAll(() => {
    try { fs.mkdirSync(SCREENSHOT_DIR, { recursive: true }) } catch (_) {}
  })

  test('01 – App loads (no 404 on assets)', async ({ page }) => {
    const res = await page.goto('/', { waitUntil: 'networkidle', timeout: 30000 })
    expect(res?.status()).toBe(200)
    await page.waitForTimeout(2000)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '01_app_load.png'), fullPage: true })
    await expect(page.locator('#app')).toBeVisible()
  })

  test('02 – Register → Wizard → Dashboard → Users → Reports (role flow)', async ({ page }) => {
    test.setTimeout(120000)
    const email = `verify-${Date.now()}@test.local`
    const password = 'Verify123!'

    await page.goto('/register', { waitUntil: 'networkidle', timeout: 30000 })
    await page.waitForTimeout(1500)
    await page.locator('input[type="email"]').first().fill(email)
    await page.locator('input[type="text"]').first().fill('Verification Shop')
    await page.locator('input[type="password"]').first().fill(password)
    await page.locator('input[type="password"]').nth(1).fill(password)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '02_register.png'), fullPage: true })
    await page.getByRole('button', { name: /create account/i }).click()
    await expect(page).toHaveURL(/\/setup-wizard/, { timeout: 20000 })

    await waitStable(page)
    await page.locator('select').first().selectOption('pharmacy')
    await page.locator('select').nth(1).selectOption('MMK')
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '03_wizard.png'), fullPage: true })
    await page.getByRole('button', { name: /complete setup|go to dashboard/i }).click()
    await expect(page).toHaveURL(/\//, { timeout: 15000 })
    await waitStable(page, 1000)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '04_dashboard.png'), fullPage: true })

    await page.goto('/users', { waitUntil: 'networkidle' })
    await waitStable(page, 800)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '05_users.png'), fullPage: true })

    await page.goto('/reports/sales-summary', { waitUntil: 'networkidle' })
    await waitStable(page, 600)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '06_reports_sales_summary.png'), fullPage: true })
    await page.goto('/reports/sale-by-item', { waitUntil: 'networkidle' })
    await waitStable(page, 600)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '07_reports_sale_by_item.png'), fullPage: true })
    await page.goto('/reports/shift', { waitUntil: 'networkidle' })
    await waitStable(page, 600)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '08_reports_shift.png'), fullPage: true })
  })
})
