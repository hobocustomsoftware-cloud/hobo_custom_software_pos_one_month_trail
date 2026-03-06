/**
 * Lightweight User Simulation – Playwright
 * Run: node simulate.js
 * Requires: npm install playwright (or use existing @playwright/test)
 */
import { chromium } from 'playwright'
import path from 'path'
import fs from 'fs'

const BASE_URL = process.env.BASE_URL || 'http://localhost:5173'
const USERNAME = process.env.POS_USERNAME || 'admin'
const PASSWORD = process.env.POS_PASSWORD || 'admin'

const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
const outputDir = path.join('simulations', `run_${timestamp}`)

let step = 0

/** Run an action, then take a screenshot. Screenshots go to simulations/run_[timestamp]/stepN_name.png */
async function takeStep(page, name, action) {
  step++
  await action()
  const safeName = name.replace(/\s+/g, '_').replace(/[^a-z0-9_]/gi, '').toLowerCase() || 'step'
  const filename = `step${step}_${safeName}.png`
  const filepath = path.join(outputDir, filename)
  await page.screenshot({ path: filepath, fullPage: false })
  console.log(`  Screenshot: ${filename}`)
}

async function run() {
  fs.mkdirSync(outputDir, { recursive: true })
  console.log(`Output folder: ${outputDir}\n`)

  const browser = await chromium.launch({ headless: true })
  const page = await browser.newPage()
  await page.setViewportSize({ width: 1280, height: 720 })

  try {
    await takeStep(page, 'login_page', async () => {
      await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' })
      await page.waitForLoadState('networkidle').catch(() => {})
    })

    await takeStep(page, 'after_login', async () => {
      await page.getByPlaceholder('Enter your username').fill(USERNAME)
      await page.getByPlaceholder('••••••••').fill(PASSWORD)
      await page.getByRole('button', { name: /Sign In|Logging in/ }).click()
      await page.waitForURL(/\/(app\/)?($|\?|#)/, { timeout: 10000 }).catch(() => {})
      await page.waitForTimeout(1500)
    })

    await takeStep(page, 'dashboard', async () => {
      await page.waitForSelector('text=Total Revenue', { timeout: 8000 }).catch(() => {})
      await page.waitForTimeout(500)
    })

    await takeStep(page, 'bento_click', async () => {
      const card = page.getByText('USD Rate').first()
      await card.scrollIntoViewIfNeeded().catch(() => {})
      await card.click().catch(() => {})
      await page.waitForTimeout(800)
    })

    await takeStep(page, 'ai_insight', async () => {
      const insightCard = page.getByText('Smart Business Insight').first()
      await insightCard.scrollIntoViewIfNeeded()
      await page.waitForTimeout(600)
    })
  } finally {
    await browser.close()
  }

  console.log(`\nDone. Screenshots saved in: ${path.resolve(outputDir)}`)
}

run().catch((e) => {
  console.error(e)
  process.exit(1)
})
