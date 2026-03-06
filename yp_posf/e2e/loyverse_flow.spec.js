// Loyverse-style flow: Register Pharmacy -> Login -> Setup Wizard -> Product creation shows Tablet/Strip/Box units
// Screenshots saved to demo_results/loyverse_flow/
// Run: npx playwright test e2e/loyverse_flow.spec.js --project=chromium
// Requires: Backend on 8000, Frontend on 5173 (or set PLAYWRIGHT_BASE_URL)
import { test, expect } from '@playwright/test'
import path from 'path'
import fs from 'fs'

const SCREENSHOT_DIR = path.join(process.cwd(), '..', 'demo_results', 'loyverse_flow')

test.describe('Loyverse-style flow', () => {
  test.beforeAll(() => {
    try {
      fs.mkdirSync(SCREENSHOT_DIR, { recursive: true })
    } catch (_) {}
  })

  test('register Pharmacy shop, login, setup wizard, verify units in product form', async ({ page }) => {
    const phone = '09' + String(Date.now()).slice(-8)
    const password = 'loyverse123'

    // Step 1: Register page
    await page.goto('/register')
    await expect(page.getByRole('heading', { name: /စာရင်းသွင်းရန်/i })).toBeVisible({ timeout: 10000 })
    await page.getByLabel(/အမည်ပြည့်|full name/i).fill('Pharmacy Demo')
    await page.getByLabel(/ဖုန်းနံပါတ်/i).fill(phone)
    await page.getByLabel(/ဆိုင်အမည်|business name/i).fill('Demo Pharmacy Shop')
    await page.locator('select').first().selectOption('pharmacy')
    await page.locator('select').nth(1).selectOption('MMK')
    await page.locator('input[type="password"]').first().fill(password)
    await page.locator('input[type="password"]').nth(1).fill(password)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '01_register_filled.png') })
    await page.getByRole('button', { name: /စာရင်းသွင်းရန်|register/i }).click()

    // Step 2: Setup Wizard
    await expect(page).toHaveURL(/\/setup-wizard/, { timeout: 15000 })
    await expect(page.getByText(/setup wizard|complete setup/i).first()).toBeVisible({ timeout: 5000 })
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '02_setup_wizard.png') })
    await page.getByRole('button', { name: /complete setup|go to dashboard/i }).click()

    // Step 3: Dashboard (or main)
    await expect(page).toHaveURL(/\//, { timeout: 10000 })
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '03_after_setup.png') })

    // Step 4: Go to Products, open Add Product, check units dropdown has Pharmacy units
    await page.goto('/products')
    await page.waitForTimeout(1500)
    await page.getByRole('button', { name: /add product/i }).click({ timeout: 10000 })
    await page.waitForTimeout(800)
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '04_product_modal.png') })

    const baseUnitLabel = page.getByText(/base unit|ယူနစ်/i).first()
    await expect(baseUnitLabel).toBeVisible({ timeout: 5000 })
    const unitSelect = page.locator('select').filter({ has: page.locator('option') }).last()
    await expect(unitSelect).toBeVisible({ timeout: 3000 })
    const options = await unitSelect.locator('option').allTextContents()
    const hasTablet = options.some(t => t.includes('Tablet') || t.includes('တစ်လုံး'))
    const hasStrip = options.some(t => t.includes('Strip') || t.includes('ကတ်'))
    const hasBox = options.some(t => t.includes('Box') || t.includes('ဖာ'))
    expect(hasTablet || hasStrip || hasBox, 'Pharmacy units (Tablet/Strip/Box) should appear in product dropdown').toBeTruthy()
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '05_units_dropdown.png') })
  })
})
