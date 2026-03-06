/**
 * business_sim.js – 30-day business simulation for multiple shop types
 * Run: node business_sim.js
 * Requires: Backend + Frontend running; Playwright installed.
 *
 * Folder output: simulations/[shop_slug]/day_1.png, day_2.png, ... day_7_insight.png (on days 7,14,21,30)
 */

import { chromium } from 'playwright'
import path from 'path'
import fs from 'fs'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

const BASE_URL = process.env.BASE_URL || 'http://localhost:5173'
const USERNAME = process.env.POS_USERNAME || 'admin'
const PASSWORD = process.env.POS_PASSWORD || 'admin'
const HEADLESS = process.env.HEADLESS !== '0'

// ─── Shop configs (add more here for new shop types) ─────────────────────────
/** @type {Record<string, { name: string; items: string[]; priceMinL: number; priceMaxL: number }>} */
const SHOP_CONFIGS = {
  solar_solutions: {
    name: 'Solar Solutions',
    items: ['Inverter', 'Panel', 'Battery'],
    priceMinL: 5,
    priceMaxL: 40,
  },
  home_appliances: {
    name: 'Home Appliances',
    items: ['TV', 'Aircon', 'Fridge'],
    priceMinL: 3,
    priceMaxL: 20,
  },
}

const USD_RATE_MIN = 3900
const USD_RATE_MAX = 4300
const ORDERS_PER_DAY_MIN = 5
const ORDERS_PER_DAY_MAX = 10
const AI_INSIGHT_DAYS = [7, 14, 21, 30]

// ─── Helpers ────────────────────────────────────────────────────────────────
function randomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min
}

function pickRandom(arr) {
  return arr[randomInt(0, arr.length - 1)]
}

/** Fluctuating USD rate for the day (3900–4300 MMK) */
function getUsdRateForDay(day) {
  const t = (day / 30) * Math.PI * 2
  const mid = (USD_RATE_MIN + USD_RATE_MAX) / 2
  const amp = (USD_RATE_MAX - USD_RATE_MIN) / 2
  return Math.round(mid + amp * Math.sin(t) + randomInt(-50, 50))
}

/**
 * Generate 5–10 orders for a day. Each order = list of { productName, qty }.
 * @param {number} day
 * @param {{ items: string[] }} config
 */
function generateOrdersForDay(day, config) {
  const numOrders = randomInt(ORDERS_PER_DAY_MIN, ORDERS_PER_DAY_MAX)
  const orders = []
  for (let i = 0; i < numOrders; i++) {
    const numLines = randomInt(1, 3)
    const lines = []
    for (let j = 0; j < numLines; j++) {
      lines.push({ productName: pickRandom(config.items), qty: randomInt(1, 2) })
    }
    orders.push(lines)
  }
  return orders
}

// ─── Page actions ───────────────────────────────────────────────────────────
async function ensureLogin(page) {
  await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' })
  await page.waitForLoadState('networkidle').catch(() => {})
  const loginInput = page.getByPlaceholder('Enter your username')
  if (await loginInput.isVisible().catch(() => false)) {
    await loginInput.fill(USERNAME)
    await page.getByPlaceholder('••••••••').fill(PASSWORD)
    await page.getByRole('button', { name: /Sign In|Logging in/ }).click()
    await page.waitForURL(/\/(app\/)?($|\?|#)|(\/sales)|(\/dashboard)/, { timeout: 15000 }).catch(() => {})
    await page.waitForTimeout(1500)
  }
}

async function goToPos(page) {
  await page.goto(new URL('/sales/pos', BASE_URL).href, { waitUntil: 'domcontentloaded' })
  await page.waitForLoadState('networkidle').catch(() => {})
  await page.waitForSelector('text=Sales Terminal', { timeout: 10000 }).catch(() => {})
  await page.waitForTimeout(500)
}

async function setUsdRate(page, rate) {
  const input = page.locator('input[type="number"]').first()
  await input.fill(String(rate))
  await page.waitForTimeout(300)
}

async function addProductToCart(page, productName) {
  const search = page.getByPlaceholder('Scan Barcode or Search...')
  await search.fill(productName)
  await page.waitForTimeout(600)
  const card = page.locator('.cursor-pointer').filter({ hasText: productName }).first()
  const found = await card.isVisible().catch(() => false)
  if (found) await card.click()
  else await page.locator('.cursor-pointer').first().click()
  await page.waitForTimeout(300)
}

async function submitOrder(page) {
  await page.getByRole('button', { name: /Confirm & Request/ }).click()
  await page.waitForTimeout(2000)
  const createNew = page.getByRole('button', { name: /Create New Order/ })
  if (await createNew.isVisible().catch(() => false)) await createNew.click()
  await page.waitForTimeout(800)
}

async function goToDashboard(page) {
  await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' })
  await page.waitForLoadState('networkidle').catch(() => {})
  await page.waitForSelector('text=Total Revenue', { timeout: 10000 }).catch(() => {})
  await page.waitForTimeout(500)
}

async function screenshotAiInsight(page, filepath) {
  const insight = page.getByText('Smart Business Insight').first()
  await insight.scrollIntoViewIfNeeded()
  await page.waitForTimeout(800)
  await page.screenshot({ path: filepath, fullPage: false })
}

// ─── One day simulation for one shop ───────────────────────────────────────
/**
 * @param {import('playwright').Page} page
 * @param {number} day
 * @param {{ name: string; items: string[]; priceMinL: number; priceMaxL: number }} config
 * @param {string} shopSlug
 * @param {string} outputDir
 */
async function runDay(page, day, config, shopSlug, outputDir) {
  const usdRate = getUsdRateForDay(day)
  const orders = generateOrdersForDay(day, config)

  await goToPos(page)
  await setUsdRate(page, usdRate)

  for (const lines of orders) {
    const search = page.getByPlaceholder('Scan Barcode or Search...')
    await search.fill('')
    await page.waitForTimeout(400)
    for (const line of lines) {
      for (let q = 0; q < line.qty; q++) await addProductToCart(page, line.productName)
    }
    await submitOrder(page)
  }

  await goToDashboard(page)
  const dayPath = path.join(outputDir, `day_${day}.png`)
  await page.screenshot({ path: dayPath, fullPage: false })
  console.log(`    [${config.name}] Day ${day} → ${path.basename(dayPath)}`)

  if (AI_INSIGHT_DAYS.includes(day)) {
    const insightPath = path.join(outputDir, `day_${day}_insight.png`)
    await screenshotAiInsight(page, insightPath)
    console.log(`    [${config.name}] Day ${day} AI Insight → ${path.basename(insightPath)}`)
  }
}

// ─── Main ───────────────────────────────────────────────────────────────────
async function main() {
  const browser = await chromium.launch({ headless: HEADLESS })
  const page = await browser.newPage()
  await page.setViewportSize({ width: 1280, height: 720 })

  try {
    await ensureLogin(page)

    for (const [shopSlug, config] of Object.entries(SHOP_CONFIGS)) {
      const outputDir = path.join(__dirname, 'simulations', shopSlug)
      fs.mkdirSync(outputDir, { recursive: true })
      console.log(`\n[${config.name}] Output: ${outputDir}`)

      for (let day = 1; day <= 30; day++) {
        await runDay(page, day, config, shopSlug, outputDir)
      }
    }

    console.log('\nDone. Screenshots in simulations/[shop_type]/')
  } finally {
    await browser.close()
  }
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})
