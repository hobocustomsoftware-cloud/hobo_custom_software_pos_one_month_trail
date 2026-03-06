// CMD: npx playwright test e2e/screenshots-for-marketing.spec.js --project=chromium
// ကြော်ငြာမှာသုံးဖို့ စာမျက်နှာတိုင်း screenshot သိမ်းမည် (တစ်နှစ်စာဒေတာစမ်းပြီးမှ run ပါ)
//
// လိုအပ်ချက်: (၁) Backend API ဖွင့်ထားရမယ်  (၂) Frontend dev server ဖွင့်ထားရမယ်
// Port ပြောင်းရင်: $env:PLAYWRIGHT_BASE_URL='http://localhost:5175'; npx playwright test ...
// သိမ်းမယ့်နေရာ: screenshots_for_marketing/run_YYYY-MM-DD_HH-mm-ss/ (အရင် run တွေမဖျက်ပစ်ဘဲ ထပ်ထည့်သိမ်းမယ်)
import { test, expect } from '@playwright/test'
import path from 'node:path'
import fs from 'node:fs'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const SCREENSHOT_BASE = path.join(__dirname, '..', 'screenshots_for_marketing')
fs.mkdirSync(SCREENSHOT_BASE, { recursive: true })
// အရင် screenshot တွေမဖျက်ပစ်ဘဲ run တစ်ခုချင်းစီကို subfolder ထဲမှာပဲ သိမ်းမယ်
const runName = 'run_' + new Date().toISOString().slice(0, 19).replace(/T/g, '_').replace(/:/g, '-')
const SCREENSHOT_DIR = path.join(SCREENSHOT_BASE, runName)
fs.mkdirSync(SCREENSHOT_DIR, { recursive: true })

// seed_demo_users / seed_one_year ပြီးရင် owner / demo123 သုံးပါ
const LOGIN_USER = process.env.PLAYWRIGHT_LOGIN_USER || 'owner'
const LOGIN_PASS = process.env.PLAYWRIGHT_LOGIN_PASS || 'demo123'

test.describe('Screenshots for marketing', () => {
  test('login and capture screenshots of all main pages', async ({ page }) => {
    // 1) Login
    await page.goto('/login')
    await page.getByPlaceholder(/enter your username/i).fill(LOGIN_USER)
    await page.getByPlaceholder(/••••••••/).first().fill(LOGIN_PASS)
    await page.getByRole('button', { name: /sign in|login/i }).click()
    // Backend လိုပါတယ် – login success မှ Dashboard သို့ ပြောင်းမယ်
    await expect(page).toHaveURL(/\/(\?.*)?$/, { timeout: 25000 })
    await page.waitForTimeout(2000)

    const shots = [
      { path: '/', name: '01-dashboard.png' },
      { path: '/inventory', name: '02-inventory.png' },
      { path: '/products', name: '03-products.png' },
      { path: '/sales/history', name: '04-sales-history.png' },
      { path: '/sales/pos', name: '05-sales-pos.png' },
      { path: '/service', name: '06-service.png' },
      { path: '/reports/sales', name: '07-reports-sales.png' },
      { path: '/settings', name: '08-settings.png' },
    ]

    for (const { path: route, name } of shots) {
      await page.goto(route)
      await page.waitForLoadState('networkidle').catch(() => {})
      await page.waitForTimeout(1200)
      await page.screenshot({
        path: path.join(SCREENSHOT_DIR, name),
        fullPage: true,
      })
    }
  })
})
