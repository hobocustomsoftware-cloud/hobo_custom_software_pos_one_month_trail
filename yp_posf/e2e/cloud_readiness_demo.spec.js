// Cloud Readiness Demo: Register -> Setup Wizard -> Manager + 2 Outlets -> Inventory (Product, Purchase, Transfer) -> POS Sale -> Reports
// Run: PLAYWRIGHT_BASE_URL=http://localhost:80 npx playwright test e2e/cloud_readiness_demo.spec.js --project=chromium --headed
// Screenshots: demo_results/cloud_readiness/
import { test, expect } from '@playwright/test'
import path from 'path'
import fs from 'fs'

const SCREENSHOT_DIR = path.join(process.cwd(), '..', 'demo_results', 'cloud_readiness')

async function waitForStable(page, extraMs = 500) {
  await page.waitForLoadState('networkidle')
  await page.evaluate(() => document.fonts && document.fonts.ready).catch(() => {})
  await page.waitForTimeout(400)
  await page.locator('.animate-spin, [role="progressbar"]').first().waitFor({ state: 'hidden', timeout: 6000 }).catch(() => {})
  await page.waitForTimeout(extraMs)
}

test.describe('Cloud Readiness Demo', () => {
  test.beforeAll(() => {
    try { fs.mkdirSync(SCREENSHOT_DIR, { recursive: true }) } catch (_) {}
  })

  test('Full journey: Register -> Wizard -> Manager & Outlets -> Inventory -> POS -> Reports', async ({ page }) => {
    test.setTimeout(180000)
    const email = `cloud-${Date.now()}@demo.local`
    const password = 'CloudDemo123!'
    const shopName = 'Cloud Readiness Shop'

    // Step 1: Register
    await page.goto('/register', { waitUntil: 'networkidle', timeout: 60000 })
    await page.waitForTimeout(2000)
    const emailInput = page.locator('input[type="email"]').first()
    await emailInput.waitFor({ state: 'visible', timeout: 15000 })
    await emailInput.fill(email)
    await page.locator('input[type="text"]').first().fill(shopName)
    const pwInputs = page.locator('input[type="password"]')
    await pwInputs.nth(0).fill(password)
    await pwInputs.nth(1).fill(password)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'flow_01_register.png'), fullPage: true })
    await page.getByRole('button', { name: /create account/i }).click()
    await expect(page).toHaveURL(/\/setup-wizard/, { timeout: 20000 })

    // Step 2: Setup Wizard
    await waitForStable(page)
    await page.locator('select').first().selectOption('pharmacy')
    await page.locator('select').nth(1).selectOption('MMK')
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'flow_02_wizard.png'), fullPage: true })
    await page.getByRole('button', { name: /complete setup|go to dashboard/i }).click()
    await expect(page).toHaveURL(/\//, { timeout: 15000 })
    await waitForStable(page)

    // Step 3: Create Manager user
    await page.goto('/users')
    await waitForStable(page)
    await page.getByRole('button', { name: /add new user/i }).click()
    await page.waitForTimeout(500)
    await page.getByLabel(/username/i).fill('manager1')
    await page.locator('input[type="password"]').fill('ManagerPass1!')
    await page.locator('select').filter({ has: page.locator('option') }).selectOption({ index: 1 })
    await page.getByRole('button', { name: /save|add|create/i }).click()
    await page.waitForTimeout(2000)

    // Step 3b: Setup 2 Outlets (Sites)
    await page.goto('/shop-locations')
    await waitForStable(page)
    for (let i = 1; i <= 2; i++) {
      const btn = page.getByRole('button', { name: /ဆိုင်အသစ်|new site|add site/i })
      if (await btn.isVisible().catch(() => false)) {
        await btn.click()
        await page.waitForTimeout(500)
        await page.getByLabel(/ဆိုင်အမည်|site.*name|name/i).first().fill(`Outlet ${i}`)
        await page.getByRole('button', { name: /သိမ်းမည်|save/i }).click()
        await page.waitForTimeout(1500)
      }
    }
    await page.waitForTimeout(1000)

    // Step 4: Inventory - Add product (Purchase Unit Box -> Strip), Purchase 10 Boxes, Transfer 2
    await page.goto('/items/list')
    await waitForStable(page)
    await page.getByRole('button', { name: /add product/i }).click()
    await waitForStable(page, 300)
    await page.getByLabel(/product name/i).fill('Demo Medicine')
    await page.getByLabel(/cost price/i).fill('100')
    await page.getByLabel(/retail price/i).fill('150')
    const baseLabel = page.getByText(/base unit|ယူနစ်/i).first()
    if (await baseLabel.isVisible().catch(() => false)) {
      const selects = page.locator('select')
      const n = await selects.count()
      for (let i = 0; i < n; i++) {
        const opts = await selects.nth(i).locator('option').allTextContents()
        if (opts.some(t => /strip|box|tablet/i.test(t))) {
          await selects.nth(i).selectOption({ index: 1 })
          if (i + 1 < n) await selects.nth(i + 1).selectOption({ index: 1 })
          await page.getByLabel(/conversion factor/i).fill('10').catch(() => {})
          break
        }
      }
    }
    await page.getByRole('button', { name: /save product/i }).click()
    await page.waitForTimeout(2500)

    await page.goto('/inventory/purchase-orders')
    await waitForStable(page)
    const addPoBtn = page.getByRole('button', { name: /add|create|new.*purchase/i }).first()
    if (await addPoBtn.isVisible().catch(() => false)) {
      await addPoBtn.click()
      await page.waitForTimeout(1000)
      await page.getByText('Demo Medicine').first().click().catch(() => {})
      await page.waitForTimeout(500)
      await page.locator('input[type="number"]').first().fill('10')
      await page.getByRole('button', { name: /save|submit|create/i }).first().click().catch(() => {})
      await page.waitForTimeout(2000)
    }

    await page.goto('/inventory/transfer-orders')
    await waitForStable(page)
    const addTrBtn = page.getByRole('button', { name: /add|create|transfer/i }).first()
    if (await addTrBtn.isVisible().catch(() => false)) {
      await addTrBtn.click()
      await page.waitForTimeout(1000)
      await page.locator('input[type="number"]').first().fill('2')
      await page.getByRole('button', { name: /save|submit|transfer/i }).first().click().catch(() => {})
      await page.waitForTimeout(2000)
    }

    await page.goto('/items/list')
    await waitForStable(page)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'flow_03_inventory.png'), fullPage: true })

    // Step 5: POS - sell 5 Strips
    await page.goto('/sales/pos')
    await waitForStable(page, 800)
    const productCard = page.getByText('Demo Medicine').first()
    await expect(productCard).toBeVisible({ timeout: 10000 })
    await productCard.click()
    await page.waitForTimeout(600)
    const qtyInput = page.locator('input[type="number"]').first()
    if (await qtyInput.isVisible().catch(() => false)) {
      await qtyInput.fill('5')
    } else {
      const plusBtn = page.getByRole('button', { name: /\+|add/i }).first()
      for (let i = 0; i < 4; i++) await plusBtn.click().catch(() => {})
    }
    await page.waitForTimeout(400)
    const payBtn = page.getByRole('button', { name: /ငွေသား|cash|pay|ပေးချေ/i }).first()
    await expect(payBtn).toBeVisible({ timeout: 5000 })
    await payBtn.click()
    await page.waitForTimeout(2000)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'flow_04_pos_sale.png'), fullPage: true })

    // Step 6: Reports
    await page.goto('/reports/sales-summary')
    await waitForStable(page)
    await page.goto('/reports/sale-by-item')
    await waitForStable(page)
    await page.goto('/reports/shift')
    await waitForStable(page)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'flow_05_reports.png'), fullPage: true })
  })
})
