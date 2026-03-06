#!/usr/bin/env node
/**
 * Run E2E demo in headed mode: Register -> Setup Wizard -> Create Product (Purchase Unit) -> Sale.
 * Sets PLAYWRIGHT_DEMO_FLOW=1 and PLAYWRIGHT_HEADED=1 then runs feature_verification.spec.js.
 * Usage: npm run test:e2e:demo   (from yp_posf) or node scripts/run-e2e-demo.js
 */
import { spawn } from 'child_process'
import path from 'path'
import fs from 'fs'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const root = path.join(__dirname, '..')
const screenshotDir = path.join(root, '..', 'demo_results', 'feature_verification')

const env = {
  ...process.env,
  PLAYWRIGHT_DEMO_FLOW: '1',
  PLAYWRIGHT_HEADED: '1',
  PLAYWRIGHT_BASE_URL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:80',
}
const isWin = process.platform === 'win32'
const playwrightBin = path.join(root, 'node_modules', '.bin', isWin ? 'playwright.cmd' : 'playwright')
const child = spawn(
  playwrightBin,
  ['test', 'e2e/feature_verification.spec.js', '--project=chromium'],
  { cwd: root, env, stdio: 'inherit', shell: isWin }
)
child.on('exit', (code) => {
  if (code !== 0) process.exit(code)
  if (!fs.existsSync(screenshotDir)) {
    console.log('\n[run-e2e-demo] No screenshot dir yet:', screenshotDir)
    return
  }
  const files = fs.readdirSync(screenshotDir).filter((f) => f.endsWith('.png')).sort()
  console.log('\n=== Screenshots in demo_results/feature_verification/ ===')
  console.log(`Total: ${files.length} files`)
  files.forEach((f) => console.log('  ', f))
  if (files.length !== 31) console.log(`\nExpected 31 screenshots; got ${files.length}.`)
  else console.log('\nAll 31 screenshots saved.')
})
