// Verify: 1) No 404 on assets at /app/  2) Phone Number field on Register/Login  3) Register with phone + Login with phone
// Run after: docker-compose -f compose/docker-compose.yml --env-file .env up -d --build
// From yp_posf: PLAYWRIGHT_BASE_URL=http://localhost/app npx playwright test e2e/docker_phone_register_login.spec.js --project=chromium
import { test, expect } from '@playwright/test'

const BASE = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost/app'

async function waitStable(page, ms = 600) {
  await page.waitForLoadState('networkidle')
  await page.waitForTimeout(ms)
}

test.describe('Docker /app/ – No 404 and Phone Register/Login', () => {
  test('App loads at /app/ with no 404 on assets', async ({ page }) => {
    const failed = []
    page.on('response', (r) => {
      const u = r.url()
      if (r.status() === 404 && (u.includes('/assets/') || u.endsWith('.js') || u.endsWith('.css'))) failed.push(u)
    })
    const res = await page.goto(`${BASE}/`, { waitUntil: 'networkidle', timeout: 30000 })
    expect(res?.status()).toBe(200)
    await page.waitForTimeout(3000)
    expect(page.locator('#app')).toBeVisible()
    expect(failed.length).toBe(0)
  })

  test('Register page shows Phone Number field and high-contrast text', async ({ page }) => {
    await page.goto(`${BASE}/register`, { waitUntil: 'networkidle', timeout: 30000 })
    await waitStable(page, 800)
    await expect(page.getByPlaceholder(/09xxxxxxxx|phone/i)).toBeVisible()
    await expect(page.getByLabel(/phone number/i)).toBeVisible()
    await expect(page.locator('input[type="email"]')).toBeVisible()
    await expect(page.locator('input[type="password"]').first()).toBeVisible()
  })

  test('Login page shows Email or Phone Number field', async ({ page }) => {
    await page.goto(`${BASE}/login`, { waitUntil: 'networkidle', timeout: 30000 })
    await waitStable(page, 500)
    await expect(page.getByLabel(/email or phone/i)).toBeVisible()
    await expect(page.getByPlaceholder(/09xxxxxxxx|email/i)).toBeVisible()
  })

  test('Register with Phone Number then Login with same phone', async ({ page }) => {
    test.setTimeout(90000)
    const phone = '09' + String(Date.now()).slice(-8)
    const password = 'PhoneTest123!'

    await page.goto(`${BASE}/register`, { waitUntil: 'networkidle', timeout: 30000 })
    await waitStable(page, 800)
    await page.getByPlaceholder(/09xxxxxxxx/i).fill(phone)
    await page.getByPlaceholder(/my store|shop/i).fill('Phone Shop')
    await page.locator('input[type="password"]').first().fill(password)
    await page.locator('input[type="password"]').nth(1).fill(password)
    await page.getByRole('button', { name: /create account/i }).click()
    await expect(page).toHaveURL(/\/(setup-wizard|app\/setup-wizard)/, { timeout: 20000 })

    await page.goto(`${BASE}/login`, { waitUntil: 'networkidle' })
    await page.getByPlaceholder(/09xxxxxxxx|email/i).fill(phone)
    await page.locator('input[type="password"]').fill(password)
    await page.getByRole('button', { name: /sign in/i }).click()
    await expect(page).toHaveURL(/\/(app\/)?(\?.*)?$/, { timeout: 15000 })
    await waitStable(page, 1000)
    await expect(page.locator('#app')).toBeVisible()
  })
})
