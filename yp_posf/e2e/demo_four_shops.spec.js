/**
 * Full E2E Demo for 4 shops: Pharmacy, Mobile, Electrical, Solar.
 * Saves screenshots to demo_results/<shop>/ with networkidle wait.
 * Run: npx playwright test e2e/demo_four_shops.spec.js --project=chromium
 *      DEMO_SHOP=pharmacy npx playwright test e2e/demo_four_shops.spec.js --project=chromium
 * With visible browser: add --headed
 */
import path from 'path'
import fs from 'fs'

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:5173'
const API_URL = process.env.PLAYWRIGHT_API_BASE || 'http://127.0.0.1:8000'
const ADMIN_USER = process.env.PLAYWRIGHT_LOGIN_USER || 'admin'
const ADMIN_PASS = process.env.PLAYWRIGHT_LOGIN_PASS || 'admin123'
const DEMO_SHOP = process.env.DEMO_SHOP || 'pharmacy' // pharmacy | mobile_shop | electrical | solar

const ROOT_DIR = path.join(process.cwd(), 'demo_results') // from yp_posf when run via npx playwright
const SHOP_FOLDERS = {
  pharmacy: path.join(ROOT_DIR, 'pharmacy'),
  mobile_shop: path.join(ROOT_DIR, 'mobile_shop'),
  electrical: path.join(ROOT_DIR, 'electrical'),
  solar: path.join(ROOT_DIR, 'solar'),
}

function ensureDemoFolders() {
  fs.mkdirSync(ROOT_DIR, { recursive: true })
  Object.values(SHOP_FOLDERS).forEach((dir) => fs.mkdirSync(dir, { recursive: true }))
}

function getShopDir(shop) {
  return SHOP_FOLDERS[shop] || path.join(ROOT_DIR, shop)
}

async function waitForAppReady(page, timeout = 30000) {
  await page.waitForLoadState('domcontentloaded')
  await page.waitForLoadState('networkidle').catch(() => {})
  await page.waitForTimeout(2000)
}

async function login(page, baseURL) {
  await page.goto(`${baseURL}/login`, { waitUntil: 'domcontentloaded', timeout: 20000 })
  await page.waitForLoadState('networkidle').catch(() => {})
  await page.waitForTimeout(1500)
  const userInput = page.locator('input[type="text"]').first()
  await userInput.waitFor({ state: 'visible', timeout: 10000 })
  await userInput.fill(ADMIN_USER)
  await page.locator('input[type="password"]').first().fill(ADMIN_PASS)
  await page.getByRole('button', { name: /sign in|login|ဝင်/i }).first().click()
  await page.waitForURL(/\/(\?.*)?$/, { timeout: 20000 }).catch(() => {})
  await page.waitForTimeout(3000)
}

async function capturePage(page, baseURL, url, filepath, options = {}) {
  await page.goto(`${baseURL}${url}`, { waitUntil: 'domcontentloaded', timeout: 20000 })
  await page.waitForLoadState('networkidle').catch(() => {})
  await page.waitForTimeout(options.waitMs || 2500)
  await page.screenshot({ path: filepath, fullPage: options.fullPage !== false })
}

test.describe('E2E Demo – Four Shops', () => {
  test.beforeAll(() => {
    ensureDemoFolders()
  })

  test('Pharmacy shop: login, capture Dashboard, Product List, Purchase History, Stock Report', async ({ page }) => {
    test.setTimeout(120000)
    if (DEMO_SHOP !== 'pharmacy' && DEMO_SHOP !== 'all') return test.skip()
    const shopDir = getShopDir('pharmacy')
    const baseURL = BASE_URL

    await page.setViewportSize({ width: 1280, height: 900 })

    await login(page, baseURL)

    await capturePage(page, baseURL, '/', path.join(shopDir, '01_dashboard.png'), { waitMs: 3000 })
    await capturePage(page, baseURL, '/products', path.join(shopDir, '02_product_list.png'))
    await capturePage(page, baseURL, '/movements', path.join(shopDir, '03_purchase_movement_history.png'))
    await capturePage(page, baseURL, '/reports/inventory', path.join(shopDir, '04_stock_report.png'))

    expect(fs.existsSync(path.join(shopDir, '01_dashboard.png'))).toBeTruthy()
    expect(fs.existsSync(path.join(shopDir, '04_stock_report.png'))).toBeTruthy()
  })

  test('Pharmacy: perform Purchase and Transfer then capture results', async ({ page }) => {
    test.setTimeout(180000)
    if (DEMO_SHOP !== 'pharmacy' && DEMO_SHOP !== 'all') return test.skip()
    const shopDir = getShopDir('pharmacy')
    const baseURL = BASE_URL

    await page.setViewportSize({ width: 1280, height: 900 })
    await login(page, baseURL)

    await page.goto(`${baseURL}/products`, { waitUntil: 'networkidle' })
    await page.waitForTimeout(1500)
    const addBtn = page.getByRole('button', { name: /add product/i }).first()
    if (await addBtn.isVisible()) {
      await addBtn.click()
      await page.waitForTimeout(1000)
      const modal = page.locator('.glass-card').filter({ has: page.getByText('Product', { exact: false }) })
      await modal.locator('input[type="text"]').first().fill('Amoxicillin')
      await modal.locator('input[type="number"]').nth(0).fill('500')
      await modal.locator('input[type="number"]').nth(1).fill('600')
      const selects = modal.locator('select')
      if ((await selects.count()) >= 4) {
        await selects.nth(2).selectOption({ label: /Strip/ })
        await selects.nth(3).selectOption({ label: /Box/ })
        await modal.locator('input[placeholder*="10"], input[step="0.01"]').last().fill('10').catch(() => {})
      }
      await page.getByRole('button', { name: /save product/i }).first().click()
      await page.waitForTimeout(2500)
    }

    await page.goto(`${baseURL}/movements`, { waitUntil: 'networkidle' })
    await page.waitForTimeout(1000)
    const purchaseBtn = page.getByRole('button', { name: /create purchase/i }).first()
    if (await purchaseBtn.isVisible()) {
      await purchaseBtn.click()
      await page.waitForTimeout(1500)
      await page.locator('select').first().selectOption({ label: /Amoxicillin/ }).catch(() => {})
      await page.locator('select').nth(1).selectOption({ label: /Box/ }).catch(() => {})
      await page.locator('input[type="number"]').first().fill('5')
      await page.locator('input[type="number"]').nth(1).fill('5000')
      await page.locator('select').last().selectOption({ label: /Main|Warehouse/ })
      await page.getByRole('button', { name: /create purchase/i }).last().click()
      await page.waitForTimeout(2500)
    }

    const recordBtn = page.getByRole('button', { name: /record movement/i }).first()
    if (await recordBtn.isVisible()) {
      await recordBtn.click()
      await page.waitForTimeout(800)
      await page.getByRole('button', { name: /switch to transfer/i }).click().catch(() => {})
      await page.waitForTimeout(500)
      await page.locator('select').first().selectOption({ label: /Amoxicillin/ }).catch(() => {})
      await page.locator('select').nth(1).selectOption({ label: /Main|Warehouse/ }).catch(() => {})
      await page.locator('select').nth(2).selectOption({ label: /Branch A/ }).catch(() => {})
      await page.locator('input[type="number"]').fill('20')
      await page.getByRole('button', { name: /confirm transfer/i }).click().catch(() => {})
      await page.waitForTimeout(2000)
    }

    await capturePage(page, baseURL, '/movements', path.join(shopDir, '05_after_purchase_transfer_movements.png'))
    await capturePage(page, baseURL, '/products', path.join(shopDir, '06_after_product_list.png'))
    await capturePage(page, baseURL, '/reports/inventory', path.join(shopDir, '07_after_stock_report.png'))
  })

  test('Mobile shop: login and capture key pages', async ({ page }) => {
    test.setTimeout(90000)
    if (DEMO_SHOP !== 'mobile_shop' && DEMO_SHOP !== 'all') return test.skip()
    const shopDir = getShopDir('mobile_shop')
    await page.setViewportSize({ width: 1280, height: 900 })
    await login(page, BASE_URL)
    await capturePage(page, BASE_URL, '/', path.join(shopDir, '01_dashboard.png'), { waitMs: 3000 })
    await capturePage(page, BASE_URL, '/products', path.join(shopDir, '02_product_list.png'))
    await capturePage(page, BASE_URL, '/movements', path.join(shopDir, '03_purchase_movement_history.png'))
    await capturePage(page, BASE_URL, '/reports/inventory', path.join(shopDir, '04_stock_report.png'))
  })

  test('Electrical shop: login and capture key pages', async ({ page }) => {
    test.setTimeout(90000)
    if (DEMO_SHOP !== 'electrical' && DEMO_SHOP !== 'all') return test.skip()
    const shopDir = getShopDir('electrical')
    await page.setViewportSize({ width: 1280, height: 900 })
    await login(page, BASE_URL)
    await capturePage(page, BASE_URL, '/', path.join(shopDir, '01_dashboard.png'), { waitMs: 3000 })
    await capturePage(page, BASE_URL, '/products', path.join(shopDir, '02_product_list.png'))
    await capturePage(page, BASE_URL, '/movements', path.join(shopDir, '03_purchase_movement_history.png'))
    await capturePage(page, BASE_URL, '/reports/inventory', path.join(shopDir, '04_stock_report.png'))
  })

  test('Solar shop: login and capture key pages', async ({ page }) => {
    test.setTimeout(90000)
    if (DEMO_SHOP !== 'solar' && DEMO_SHOP !== 'all') return test.skip()
    const shopDir = getShopDir('solar')
    await page.setViewportSize({ width: 1280, height: 900 })
    await login(page, BASE_URL)
    await capturePage(page, BASE_URL, '/', path.join(shopDir, '01_dashboard.png'), { waitMs: 3000 })
    await capturePage(page, BASE_URL, '/products', path.join(shopDir, '02_product_list.png'))
    await capturePage(page, BASE_URL, '/movements', path.join(shopDir, '03_purchase_movement_history.png'))
    await capturePage(page, BASE_URL, '/reports/inventory', path.join(shopDir, '04_stock_report.png'))
  })
})
