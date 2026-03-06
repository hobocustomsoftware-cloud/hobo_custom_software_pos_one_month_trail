// CMD ကနေ screenshot ထုတ်ရန်: npx playwright test --project=chromium
// ကြော်ငြာ/မာကကတ်တင်း အတွက် စာမျက်နှာတိုင်း ဓာတ်ပုံ သိမ်းမည်
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  outputDir: './e2e/test-results',
  snapshotPathTemplate: '{testDir}/__screenshots__/{testFileName}/{arg}{ext}',
  timeout: 120000,
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:5173',
    trace: 'off',
    screenshot: 'only-on-failure',
    video: 'off',
    headless: !(process.env.PLAYWRIGHT_HEADED === '1' || process.env.PLAYWRIGHT_HEADED === 'true'),
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
})
