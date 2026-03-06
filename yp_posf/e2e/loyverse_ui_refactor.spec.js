// Loyverse UI refactor: Sidebar + Tabs (Sales Summary, Item List) screenshots
// Run: npx playwright test e2e/loyverse_ui_refactor.spec.js --project=chromium
// Requires: Backend on 8000, Frontend on 5173 (or PLAYWRIGHT_BASE_URL); logged-in user
import { test, expect } from '@playwright/test'
import path from 'path'
import fs from 'fs'

const SCREENSHOT_DIR = path.join(process.cwd(), '..', 'demo_results', 'loyverse_ui_refactor')

test.describe('Loyverse UI refactor', () => {
  test.beforeAll(() => {
    try {
      fs.mkdirSync(SCREENSHOT_DIR, { recursive: true })
    } catch (_) {}
  })

  test('sidebar and Sales Summary tabs screenshot', async ({ page }) => {
    await page.goto('/login')
    const loginUser = process.env.PLAYWRIGHT_LOGIN_USER || '09999999999'
    const loginPass = process.env.PLAYWRIGHT_LOGIN_PASS || 'demo123'
    await page.getByPlaceholder(/09|ဖုန်း|email/i).fill(loginUser)
    await page.getByPlaceholder(/••••••••/).first().fill(loginPass)
    await page.getByRole('button', { name: /sign in|login/i }).click()
    await expect(page).toHaveURL(/\/(setup-wizard)?(\?.*)?$/, { timeout: 15000 })
    if (page.url().includes('setup-wizard')) {
      await page.getByRole('button', { name: /complete setup|go to dashboard/i }).click()
      await page.waitForURL(/\//, { timeout: 8000 })
    }
    await page.goto('/reports/sales-summary')
    await page.waitForTimeout(1500)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '01_sidebar_and_sales_summary.png'), fullPage: false })
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '02_sales_summary_tabs.png'), fullPage: true })
  })

  test('Item List page with tabs screenshot', async ({ page }) => {
    await page.goto('/login')
    const loginUser = process.env.PLAYWRIGHT_LOGIN_USER || '09999999999'
    const loginPass = process.env.PLAYWRIGHT_LOGIN_PASS || 'demo123'
    await page.getByPlaceholder(/09|ဖုန်း|email/i).fill(loginUser)
    await page.getByPlaceholder(/••••••••/).first().fill(loginPass)
    await page.getByRole('button', { name: /sign in|login/i }).click()
    await expect(page).toHaveURL(/\/(setup-wizard)?(\?.*)?$/, { timeout: 15000 })
    if (page.url().includes('setup-wizard')) {
      await page.getByRole('button', { name: /complete setup|go to dashboard/i }).click()
      await page.waitForURL(/\//, { timeout: 8000 })
    }
    await page.goto('/items/list')
    await page.waitForTimeout(1500)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '03_item_list_tabs.png'), fullPage: true })
  })
})
