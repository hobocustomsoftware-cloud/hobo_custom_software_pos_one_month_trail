/**
 * simulate_machinery_shop.js – 7-day sales simulation: Heavy Machinery & Electronic Shop
 * Run: node simulate_machinery_shop.js
 * Requires: Backend + Frontend running. Playwright: npm install playwright && npx playwright install chromium
 *
 * Output folder: simulations/machinery_shop/
 *   - 1.png … 7.png (dashboard after each day)
 *   - 3_insight.png, 7_insight.png (AI Insight card on day 3 and 7)
 */

import { chromium } from 'playwright'
import path from 'path'
import fs from 'fs'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

const BASE_URL = process.env.BASE_URL || 'http://localhost:5173'
const USERNAME = process.env.POS_USERNAME || 'admin'
const PASSWORD = process.env.POS_PASSWORD || 'admin'

const OUT_DIR = path.resolve(__dirname, 'simulations', 'machinery_shop')

// Heavy Machinery & Electronic Shop – single shop config
const SHOP = {
  name: 'Heavy Machinery & Electronic Shop',
  items: [
    '5kW Inverter',
    'Heavy Duty Motor',
    'Industrial Drill',
    'Solar Panel 550W',
    'Inverter AC Unit',
  ],
  priceMin: 500_000,
  priceMax: 5_000_000,
}
const DAYS = 7
const ORDERS_MIN = 2
const ORDERS_MAX = 4
const USD_MIN = 3900
const USD_MAX = 4200
const AI_INSIGHT_DAYS = [3, 7]

const rand = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min
const pick = (arr) => arr[rand(0, arr.length - 1)]

function getUsdForDay() {
  return rand(USD_MIN, USD_MAX)
}

function generateOrders() {
  const n = rand(ORDERS_MIN, ORDERS_MAX)
  return Array.from({ length: n }, () => [{ productName: pick(SHOP.items), qty: 1 }])
}

async function login(page) {
  await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' })
  const needLogin = await page.getByPlaceholder('Enter your username').isVisible().catch(() => false)
  if (!needLogin) return
  await page.getByPlaceholder('Enter your username').fill(USERNAME)
  await page.getByPlaceholder('••••••••').fill(PASSWORD)
  await page.getByRole('button', { name: /Sign In|Logging in/ }).click()
  await page.waitForURL(/\/(app\/)?($|\?|#)|(\/sales)/, { timeout: 8_000 }).catch(() => {})
  await page.waitForTimeout(300)
}

async function runDay(page, day) {
  const usd = getUsdForDay()
  const orders = generateOrders()

  try {
    await page.goto(new URL('/sales/pos', BASE_URL).href, { waitUntil: 'domcontentloaded', timeout: 8_000 })
    await page.waitForSelector('text=Sales Terminal', { timeout: 5_000 })

    const usdInput = page.locator('input[type="number"]').first()
    await usdInput.fill(String(usd))
    await page.waitForTimeout(150)

    for (const lines of orders) {
      for (const { productName, qty } of lines) {
        for (let i = 0; i < qty; i++) {
          await page.getByPlaceholder('Scan Barcode or Search...').fill(productName)
          await page.waitForTimeout(250)
          const card = page.locator('.cursor-pointer').filter({ hasText: productName }).first()
          if (await card.isVisible().catch(() => false)) await card.click()
          else await page.locator('.cursor-pointer').first().click()
          await page.waitForTimeout(150)
        }
      }
      await page.getByRole('button', { name: /Confirm & Request/ }).click()
      await page.waitForTimeout(700)
      const createBtn = page.getByRole('button', { name: /Create New Order/ })
      if (await createBtn.isVisible().catch(() => false)) await createBtn.click()
      await page.waitForTimeout(250)
    }
  } catch (e) {
    console.log(`  Day ${day} orders skip:`, e.message || e)
  }

  await page.goto(BASE_URL, { waitUntil: 'domcontentloaded', timeout: 8_000 })
  await page.waitForSelector('text=Total Revenue', { timeout: 5_000 }).catch(() => {})
  await page.waitForTimeout(400)

  const dayPath = path.resolve(OUT_DIR, `${day}.png`)
  await page.screenshot({ path: dayPath })
  const dayOk = fs.existsSync(dayPath)
  console.log(`  Day ${day} → ${path.basename(dayPath)} ${dayOk ? '✓' : ''}`)

  if (AI_INSIGHT_DAYS.includes(day)) {
    const insight = page.getByText('Smart Business Insight').first()
    await insight.scrollIntoViewIfNeeded()
    await page.waitForTimeout(300)
    const insightPath = path.resolve(OUT_DIR, `${day}_insight.png`)
    await page.screenshot({ path: insightPath })
    const insightOk = fs.existsSync(insightPath)
    console.log(`  Day ${day} AI Insight → ${path.basename(insightPath)} ${insightOk ? '✓' : ''}`)
  }
}

async function main() {
  fs.mkdirSync(OUT_DIR, { recursive: true })
  console.log('Heavy Machinery & Electronic Shop – 7 days')
  console.log('Output:', OUT_DIR, '\n')

  const browser = await chromium.launch({ headless: true })
  const page = await browser.newPage()
  page.setDefaultTimeout(8_000)
  await page.setViewportSize({ width: 1280, height: 720 })

  let screenshots = []
  try {
    await login(page)
    for (let day = 1; day <= DAYS; day++) {
      await runDay(page, day)
    }
    if (fs.existsSync(OUT_DIR)) {
      screenshots = fs.readdirSync(OUT_DIR).filter((f) => f.endsWith('.png')).sort()
    }
  } catch (e) {
    console.error('Error:', e.message || e)
  } finally {
    await browser.close()
  }

  console.log('\nScreenshots:', screenshots.length)
  console.log('Folder:', OUT_DIR)
  screenshots.forEach((f) => console.log('  -', f))
  if (screenshots.length === 0) {
    console.log('  (No screenshots saved – check Backend + Frontend are running and path is writable.)')
  }
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})
