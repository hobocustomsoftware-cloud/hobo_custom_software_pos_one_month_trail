/**
 * E2E Multi-Shop & Multi-Role Workflow.
 * Prerequisite: Owner creates Shop A (Fixed), Shop B (Roaming), Staff role, staff_fixed and staff_roaming.
 * Scenario 1: Fixed staff (Shop A). Scenario 2: Roaming staff (Shop A -> Shop B). Scenario 3: Owner verification.
 *
 * Run: npx playwright test tests/e2e_stress_test.spec.js --project=chromium
 */
const { test, expect } = require('@playwright/test')
const fs = require('fs')
const path = require('path')

const reportBase = path.join(__dirname, '..', 'simulation_reports')
const runTimestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
const runDir = path.join(reportBase, `run_${runTimestamp}`)
const screenshotDir = path.join(runDir, 'screenshots')
const reportFile = path.join(runDir, 'business_day_report.json')

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:5173'
const API_BASE = process.env.PLAYWRIGHT_API_BASE || (BASE_URL.replace(/:\d+$/, '') + ':8000')
const OWNER_USER = process.env.PLAYWRIGHT_LOGIN_USER || 'sim_owner'
const OWNER_PASS = process.env.PLAYWRIGHT_LOGIN_PASS || 'demo123'
const STAFF_PASS = 'demo123'

const SHOP_A_NAME = 'Shop A (Fixed)'
const SHOP_B_NAME = 'Shop B (Roaming)'
const STAFF_FIXED = 'staff_fixed'
const STAFF_ROAMING = 'staff_roaming'

function isFontUrl(url) {
  return /fonts\.googleapis\.com|fonts\.gstatic\.com/i.test(url || '')
}

test('Multi-Shop & Multi-Role Workflow', async ({ page }) => {
  test.setTimeout(600000)
  await page.setViewportSize({ width: 1440, height: 1080 })

  if (!fs.existsSync(runDir)) fs.mkdirSync(runDir, { recursive: true })
  if (!fs.existsSync(screenshotDir)) fs.mkdirSync(screenshotDir, { recursive: true })

  const errorsLog = { consoleErrors: [], failedRequests: [], apiErrors: [] }

  page.on('console', (msg) => {
    const type = msg.type()
    if (type === 'error' || type === 'warning') {
      const loc = msg.location()
      errorsLog.consoleErrors.push({
        type,
        text: msg.text(),
        location: loc ? { url: loc.url, line: loc.lineNumber, column: loc.columnNumber } : null,
      })
    }
  })
  page.on('requestfailed', (request) => {
    const url = request.url()
    if (isFontUrl(url)) return
    const failure = request.failure()
    errorsLog.failedRequests.push({
      url,
      method: request.method(),
      error: failure ? failure.errorText : 'unknown',
    })
  })
  page.on('response', (response) => {
    const url = response.url()
    if (!url.includes('/api/') || isFontUrl(url)) return
    const status = response.status()
    if (status >= 400) {
      errorsLog.apiErrors.push({
        url,
        status,
        statusText: response.statusText(),
      })
    }
  })
  page.on('dialog', (dialog) => { dialog.accept().catch(() => {}) })

  const screenshot = async (name) => {
    await page.waitForTimeout(2000)
    await page.screenshot({
      path: path.join(screenshotDir, name),
      fullPage: false,
    })
  }

  const goto = async (pathname) => {
    await page.goto(`${BASE_URL}${pathname}`)
    await page.waitForLoadState('networkidle', { timeout: 60000 }).catch(() => {})
    await page.waitForTimeout(1500)
  }

  /**
   * Robust login: wait for /api/token/ 200 response, then 2000ms for localStorage to persist token.
   */
  const login = async (username, password) => {
    await goto('/login')
    await page.waitForTimeout(500)
    // Standard placeholders from Login.vue; adjust if your app uses different text
    await page.getByPlaceholder(/enter your username/i).fill(username)
    await page.getByPlaceholder(/••••••••/).fill(password)
    // Wait for login API success before any navigation
    const tokenResponse = page.waitForResponse(
      (res) => res.url().includes('/api/token/') && res.status() === 200,
      { timeout: 20000 },
    )
    await page.getByRole('button', { name: /sign in/i }).click()
    await tokenResponse
    await page.waitForTimeout(2000)
    await expect(page).toHaveURL(/\/(\?.*)?$/, { timeout: 10000 })
    await page.waitForLoadState('networkidle').catch(() => {})
    await page.waitForTimeout(1000)
  }

  /**
   * Clear state between scenarios: cookies + localStorage, then go to login page.
   */
  const logout = async () => {
    await page.context().clearCookies()
    await page.evaluate(() => localStorage.clear())
    await goto('/login')
    await page.waitForTimeout(500)
  }

  const selectLocation = async (locationId) => {
    if (!locationId) return
    await page.evaluate(
      async ({ apiBase, locationId: id }) => {
        const token = localStorage.getItem('access_token')
        if (!token) return
        await fetch(`${apiBase}/api/core/select-location/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify({ location_id: id }),
        })
      },
      { apiBase: API_BASE, locationId },
    )
    await page.waitForTimeout(800)
  }

  const doPosSale = async (sku = 'SIM-P-001') => {
    const input = page.getByPlaceholder(/scan barcode|search/i)
    await input.waitFor({ state: 'visible', timeout: 10000 }).catch(() => {})
    await input.fill(sku)
    await page.keyboard.press('Enter')
    await page.waitForTimeout(500)
    const paySelect = page.locator('select').first()
    if (await paySelect.count() > 0) await paySelect.selectOption({ index: 1 }).catch(() => {})
    await page.waitForTimeout(300)
    await page.getByRole('button', { name: /confirm & request|Submit/i }).click()
    await page.waitForTimeout(2500)
  }

  let shopASaleLocationId = null
  let shopBSaleLocationId = null

  try {
    // ---------- Prerequisite: System setup by owner ----------
    await login(OWNER_USER, OWNER_PASS)

    // ----- Create two shops (sites with sales+warehouse) via UI -----
    await goto('/shop-locations')
    await page.waitForTimeout(2000)

    for (const shopName of [SHOP_A_NAME, SHOP_B_NAME]) {
      // Click "Add Site" (ဆိုင်အသစ်) - creates a shop; UI also has "နေရာအသစ်" for location-only
      await page.getByRole('button', { name: /ဆိုင်အသစ်/ }).first().click()
      await page.waitForTimeout(600)
      const siteModal = page.locator('.fixed.inset-0').filter({ has: page.locator('input[type="checkbox"]') }).first()
      // First text input = site name (ဆိုင်အမည်)
      await siteModal.locator('input[type="text"]').first().fill(shopName)
      // Check "create sales + warehouse" so we get a sale location
      await siteModal.locator('input[type="checkbox"]').check().catch(() => {})
      await siteModal.getByRole('button', { name: /သိမ်းမည်/ }).click()
      await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {})
      await page.waitForTimeout(1500)
    }
    await screenshot('01_owner_shops_created.png')

    const locationsData = await page
      .evaluate(
        async (apiBase) => {
          const token = localStorage.getItem('access_token')
          if (!token) return []
          const r = await fetch(`${apiBase}/api/locations-admin/`, {
            headers: { Authorization: `Bearer ${token}` },
          })
          const d = await r.json()
          return Array.isArray(d) ? d : d.results || []
        },
        API_BASE,
      )
      .catch(() => [])
    const saleLocs = (locationsData || []).filter((l) => l.is_sale_location)
    shopASaleLocationId = saleLocs.find((l) => (l.name || '').includes('Shop A'))?.id
    shopBSaleLocationId = saleLocs.find((l) => (l.name || '').includes('Shop B'))?.id

    // ----- Create Staff role via UI -----
    await goto('/users/roles')
    await page.waitForTimeout(2000)
    const hasStaffRole = await page.locator('text=/Staff/i').count() > 0
    if (!hasStaffRole) {
      await page.getByRole('button', { name: /အသစ်ထည့်မယ်|ADD|Add/i }).first().click()
      await page.waitForTimeout(600)
      // Role name input (placeholder may contain "owner" or "manager")
      await page.locator('input[placeholder*="owner"], input[placeholder*="manager"], input[type="text"]').first().fill('Staff')
      await page.getByRole('button', { name: /သိမ်းမယ်|Save/i }).first().click()
      await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {})
      await page.waitForTimeout(1500)
    }

    // ----- Create staff_fixed and staff_roaming via UI -----
    await goto('/users')
    await page.waitForTimeout(2000)

    for (const { username, primaryLabel, assignedLabels } of [
      { username: STAFF_FIXED, primaryLabel: 'Shop A (Fixed) - Sales', assignedLabels: ['Shop A (Fixed) - Sales'] },
      {
        username: STAFF_ROAMING,
        primaryLabel: 'Shop A (Fixed) - Sales',
        assignedLabels: ['Shop A (Fixed) - Sales', 'Shop B (Roaming) - Sales'],
      },
    ]) {
      await page.getByRole('button', { name: /ADD NEW USER|အသစ်ထည့်/i }).first().click()
      await page.waitForTimeout(600)
      const form = page.locator('form').filter({ has: page.locator('input[type="password"]') })
      // Username: first text input in form
      await form.locator('input[type="text"]').first().fill(username)
      await form.locator('input[type="password"]').fill(STAFF_PASS)
      await form.locator('select').first().selectOption({ label: /Staff/i })
      const primarySelect = form.locator('select').nth(1)
      await primarySelect.selectOption({ label: new RegExp(primaryLabel.replace(/[()]/g, '.*'), 'i') }).catch(() => primarySelect.selectOption({ index: 1 }))
      for (const label of assignedLabels) {
        await page.getByRole('checkbox', { name: new RegExp(label.replace(/[()]/g, '.*'), 'i') }).check().catch(() => {})
      }
      await form.getByRole('button', { name: /CONFIRM|သိမ်းမယ်/i }).first().click()
      await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {})
      await page.waitForTimeout(1500)
    }
    await screenshot('02_owner_staff_created.png')

    // ---------- Scenario 1: Fixed staff (Shop A only) ----------
    await logout()
    await login(STAFF_FIXED, STAFF_PASS)

    await goto('/')
    await page.waitForTimeout(1500)
    await screenshot('03_fixed_staff_dashboard.png')

    await goto('/sales/pos')
    await page.waitForTimeout(1500)
    await doPosSale()
    await screenshot('04_fixed_staff_pos_shop_a.png')

    // ---------- Scenario 2: Roaming staff (Shop A then Shop B) ----------
    await logout()
    await login(STAFF_ROAMING, STAFF_PASS)

    await selectLocation(shopASaleLocationId)
    await goto('/sales/pos')
    await page.waitForTimeout(1500)
    await doPosSale()
    await screenshot('05_roaming_staff_pos_shop_a.png')

    await selectLocation(shopBSaleLocationId)
    await goto('/settings')
    await page.waitForTimeout(1500)
    await screenshot('06_roaming_staff_switched_to_shop_b.png')

    await goto('/sales/pos')
    await page.waitForTimeout(1500)
    await doPosSale()
    await screenshot('07_roaming_staff_pos_shop_b.png')

    // ---------- Scenario 3: Owner verification ----------
    await logout()
    await login(OWNER_USER, OWNER_PASS)

    await goto('/sales/history')
    await page.waitForTimeout(2500)
    await page.locator('table.glass-table, table').first().waitFor({ state: 'visible', timeout: 15000 }).catch(() => {})
    await screenshot('08_owner_sales_history.png')

    await goto('/reports/sales')
    await page.waitForTimeout(2500)
    await page.locator('table.glass-table, table').first().waitFor({ state: 'visible', timeout: 15000 }).catch(() => {})
    await screenshot('09_owner_reports_both_shops.png')
  } finally {
    const report = {
      timestamp: new Date().toISOString(),
      runFolder: runDir,
      baseUrl: BASE_URL,
      shopASaleLocationId,
      shopBSaleLocationId,
      ...errorsLog,
    }
    if (!fs.existsSync(runDir)) fs.mkdirSync(runDir, { recursive: true })
    try {
      fs.writeFileSync(reportFile, JSON.stringify(report, null, 2), 'utf8')
    } catch (_) {}
  }
})
