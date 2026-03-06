// Register နဲ့ Login စမ်းသပ်မှု (ပထမဦးဆုံး စာရင်းသွင်းသူ Owner ဖြစ်ခြင်း၊ တစ်ဆိုင်နဲ့တစ်ဆိုင် သီးသန့်ဖြစ်ခြင်း က Backend test မှာ စစ်ပါသည်)
//
// လိုအပ်ချက်: Backend (Django) စတင်ထားရမယ်၊ Frontend (Vite) စတင်ထားရမယ်
// ပြေးနည်း: npx playwright test e2e/register-login.spec.js --project=chromium
// ဒေတာသစ်နဲ့ စမ်းမယ်ဆိုရင်: DB မှာ user မရှိသေးတဲ့ environment (သို့) test DB သုံးပါ
import { test, expect } from '@playwright/test'

test.describe('Register and Login', () => {
  test('register first user then login and see dashboard (Loyverse-style: phone, category, currency)', async ({ page }) => {
    // 1) Register page - phone-based, Business Name, Category, Currency
    await page.goto('/register')
    await expect(page.getByRole('heading', { name: /စာရင်းသွင်းရန်/i })).toBeVisible({ timeout: 10000 })

    const phone = '09' + String(Date.now()).slice(-8)
    const password = 'e2epass123'

    await page.getByLabel(/အမည်ပြည့်|full name/i).fill('E2E Owner')
    await page.getByLabel(/ဖုန်းနံပါတ်/i).fill(phone)
    await page.getByLabel(/ဆိုင်အမည်|business name/i).fill('E2E Pharmacy')
    await page.locator('select').first().selectOption('pharmacy')
    await page.locator('select').nth(1).selectOption('MMK')
    await page.locator('input[type="password"]').first().fill(password)
    await page.locator('input[type="password"]').nth(1).fill(password)
    await page.getByRole('button', { name: /စာရင်းသွင်းရန်|register/i }).click()

    // First user: success then redirect to Setup Wizard (Loyverse-style)
    await expect(page).toHaveURL(/\/setup-wizard/, { timeout: 15000 })
    await expect(page.getByText(/setup wizard|complete setup/i).first()).toBeVisible({ timeout: 5000 })
  })

  test('login with invalid credentials shows error', async ({ page }) => {
    await page.goto('/login')
    await page.getByPlaceholder(/09|ဖုန်း|email/i).fill('09999999999')
    await page.getByPlaceholder(/••••••••/).first().fill('wrongpass')
    await page.getByRole('button', { name: /sign in|login/i }).click()

    await expect(page.getByText(/မှားယွင်း|invalid|wrong|ဝင်ရောက်၍မရ/i)).toBeVisible({ timeout: 8000 })
    await expect(page).toHaveURL(/\/login/)
  })

  test('login with valid credentials redirects to setup wizard then dashboard', async ({ page }) => {
    // Backend မှာ user ရှိမှ အောင်မြင်မယ် (seed_demo_users သို့ အရင် register လုပ်ထားပါ)
    await page.goto('/login')
    const loginUser = process.env.PLAYWRIGHT_LOGIN_USER || '09999999999'
    const loginPass = process.env.PLAYWRIGHT_LOGIN_PASS || 'demo123'

    await page.getByPlaceholder(/09|ဖုန်း|email/i).fill(loginUser)
    await page.getByPlaceholder(/••••••••/).first().fill(loginPass)
    await page.getByRole('button', { name: /sign in|login/i }).click()

    await expect(page).toHaveURL(/\/setup-wizard|\/(\?.*)?$/, { timeout: 15000 })
    await expect(page.getByText(/setup wizard|complete setup|dashboard|မူလ|welcome|sidebar|inventory|sales/i).first()).toBeVisible({ timeout: 8000 })
  })
})
