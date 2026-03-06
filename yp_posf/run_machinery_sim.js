/**
 * တစ်ခါတည်း: Vite စတင် → စောင့် → Machinery Shop Simulation (၇ ရက်) ပြေး → Vite ပိတ်
 * Run: node run_machinery_sim.js   (သို့)  npm run simulate:machinery:full
 * Backend (Django) ကို သပ်သပ် ဖွင့်ထားရမယ်။
 */
import { spawn } from 'child_process'
import { fileURLToPath } from 'url'
import path from 'path'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const BASE_URL = process.env.BASE_URL || 'http://localhost:5173'
const WAIT_MS = 200
const MAX_ATTEMPTS = 60

function waitForUrl() {
  return new Promise((resolve, reject) => {
    let attempts = 0
    const tryFetch = () => {
      fetch(BASE_URL, { method: 'GET', signal: AbortSignal.timeout(3000) })
        .then(() => resolve())
        .catch(() => {
          attempts++
          if (attempts >= MAX_ATTEMPTS) return reject(new Error('Dev server did not start in time'))
          setTimeout(tryFetch, WAIT_MS)
        })
    }
    tryFetch()
  })
}

async function main() {
  console.log('1) Starting dev server (Vite)...')
  const dev = spawn('npx', ['vite'], {
    stdio: ['ignore', 'pipe', 'pipe'],
    shell: true,
    cwd: __dirname,
  })
  dev.stdout?.on('data', (d) => process.stdout.write(d))
  dev.stderr?.on('data', (d) => process.stderr.write(d))

  console.log('2) Waiting for', BASE_URL, '...')
  await waitForUrl()
  console.log('   Ready.\n')

  console.log('3) Running Machinery Shop simulation (7 days)...')
  const sim = spawn('node', ['simulate_machinery_shop.js'], {
    stdio: 'inherit',
    shell: true,
    cwd: __dirname,
    env: { ...process.env, BASE_URL },
  })
  const exitCode = await new Promise((resolve) => sim.on('close', resolve))
  if (exitCode !== 0) {
    dev.kill()
    process.exit(exitCode)
  }

  console.log('\n4) Stopping dev server...')
  dev.kill()
  process.exit(0)
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})
