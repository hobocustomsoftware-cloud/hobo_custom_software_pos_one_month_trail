// Verification: Login/Register readable text + Item List (with ကတ် unit) screenshots.
// Run after docker-compose up: npx playwright test e2e/verification_ui_api.spec.js --project=chromium
// Or locally (Vite): baseURL defaults to 127.0.0.1:5173, use /login, /register, /items/list
import { test, expect } from '@playwright/test'
import path from 'path'
import fs from 'fs'

const OUT_DIR = path.join(process.cwd(), '..', 'demo_results', 'verification_ui_api')
const BASE = process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:5173'
const IS_APP_PREFIX = BASE.includes('80') || BASE.includes('localhost') && !BASE.includes('5173')
const P = (p) => (IS_APP_PREFIX ? `/app${p}` : p)

test.describe('UI/API verification screenshots', () => {
  test.beforeAll(() => {
    try { fs.mkdirSync(OUT_DIR, { recursive: true }) } catch (_) {}
  })

  test('Login page – readable text (deep black, 22px)', async ({ page }) => {
    await page.goto(P('/login'))
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(500)
    await page.screenshot({
      path: path.join(OUT_DIR, '01_login_readable_text.png'),
      fullPage: true,
    })
    const heading = page.locator('h1, h2, [class*="auth"]').first()
    await expect(heading).toBeVisible({ timeout: 5000 })
  })

  test('Register page – readable text', async ({ page }) => {
    await page.goto(P('/register'))
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(500)
    await page.screenshot({
      path: path.join(OUT_DIR, '02_register_readable_text.png'),
      fullPage: true,
    })
  })

  test('Item List – after login (with ကတ်/Strip unit in product management)', async ({ page }) => {
    await page.goto(P('/login'))
    await page.waitForLoadState('networkidle')
    const user = process.env.PLAYWRIGHT_LOGIN_USER || '09999999999'
    const pass = process.env.PLAYWRIGHT_LOGIN_PASS || 'demo123'
    await page.getByPlaceholder(/09|ဖုန်း|email|phone/i).fill(user)
    await page.getByPlaceholder(/password|••••••••/i).first().fill(pass)
    await page.getByRole('button', { name: /sign in|login|ဝင်ရောက်/i }).click()
    await page.waitForURL((u) => !u.includes('/login'), { timeout: 15000 })
    await page.waitForTimeout(1500)
    await page.goto(P('/items/list'))
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1500)
    await page.screenshot({
      path: path.join(OUT_DIR, '03_item_list_with_units.png'),
      fullPage: true,
    })
  })
})
