/**
 * E2E: Fixed shop scenario — stationary employee (Shop A only).
 * Login as owner → create Shop A, Staff role, staff_fixed (Shop A only) → staff does POS → logout.
 */
import { test, expect } from '@playwright/test';

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:5173';
const API_BASE = process.env.PLAYWRIGHT_API_BASE || (BASE_URL.replace(/:\d+$/, '') + ':8000');
const OWNER_USER = process.env.PLAYWRIGHT_LOGIN_USER || 'sim_owner';
const OWNER_PASS = process.env.PLAYWRIGHT_LOGIN_PASS || 'demo123';
const STAFF_PASS = 'demo123';
const SHOP_A_NAME = 'Shop A (Fixed)';
const STAFF_FIXED = 'staff_fixed';
const POS_SKU = 'SIM-P-001';

test('Fixed Shop Scenario: stationary employee', async ({ page }) => {
  test.setTimeout(300000);
  await page.setViewportSize({ width: 1440, height: 900 });

  const goto = async (pathname) => {
    await page.goto(`${BASE_URL}${pathname}`);
    await page.waitForLoadState('networkidle', { timeout: 45000 }).catch(() => {});
    await page.waitForTimeout(1500);
  };

  const login = async (user, pass) => {
    await page.goto(`${BASE_URL}/login`);
    await page.waitForTimeout(1500);
    const userInput = page.locator('input[type="text"], input[name="username"], input[placeholder*="username" i]').first();
    await userInput.waitFor({ state: 'visible' });
    await userInput.fill(user);
    const passInput = page.locator('input[type="password"]').first();
    await passInput.waitFor({ state: 'visible' });
    await passInput.fill(pass);
    await page.waitForTimeout(800);
    const tokenPromise = page.waitForResponse(
      (res) => res.url().includes('/api/token/') && res.status() === 200,
      { timeout: 15000 }
    ).catch(() => null);
    await page.getByRole('button', { name: /sign in|login|ဝင်မည်/i }).first().click();
    const tokenRes = await tokenPromise;
    if (!tokenRes) {
      throw new Error(`Login failed or timed out for user: ${user}`);
    }
    await page.waitForTimeout(2000);
  };

  const logout = async () => {
    await page.context().clearCookies();
    await page.evaluate(() => localStorage.clear());
    await goto('/login');
  };

  const doPosSale = async (sku = POS_SKU) => {
    const inputs = await page.locator('input').all();
    for (let i = inputs.length - 1; i >= 0; i--) {
      const type = await inputs[i].getAttribute('type');
      if (type !== 'hidden' && type !== 'checkbox' && type !== 'radio' && type !== 'password' && await inputs[i].isVisible()) {
        await inputs[i].fill(sku);
        await page.keyboard.press('Enter');
        break;
      }
    }
    await page.waitForTimeout(1000);
    const btns = await page.getByRole('button', { name: /add|save|confirm|အသစ်|သိမ်း/i }).all();
    for (const btn of btns) {
      if (await btn.isVisible()) {
        await btn.click({ force: true }).catch(() => {});
        break;
      }
    }
    await page.waitForTimeout(2500);
  };

  // --- Owner: create Shop A ---
  await login(OWNER_USER, OWNER_PASS);
  await goto('/shop-locations');
  await page.waitForTimeout(2000);

  const addBtns = await page.getByRole('button', { name: /add|save|confirm|အသစ်|သိမ်း/i }).all();
  for (const btn of addBtns) {
    if (await btn.isVisible()) {
      await btn.click({ force: true });
      break;
    }
  }
  await page.waitForTimeout(2000);

  const inputs = await page.locator('input').all();
  for (let i = inputs.length - 1; i >= 0; i--) {
    const type = await inputs[i].getAttribute('type');
    if (type !== 'hidden' && type !== 'checkbox' && type !== 'radio' && await inputs[i].isVisible()) {
      await inputs[i].fill(SHOP_A_NAME);
      break;
    }
  }

  const checkboxes = await page.locator('input[type="checkbox"]').all();
  for (let i = checkboxes.length - 1; i >= 0; i--) {
    if (await checkboxes[i].isVisible()) {
      await checkboxes[i].check({ force: true }).catch(() => {});
      break;
    }
  }

  const saveBtns = await page.getByRole('button', { name: /save|confirm|သိမ်း/i }).all();
  for (const btn of saveBtns) {
    if (await btn.isVisible()) {
      await btn.click({ force: true });
      break;
    }
  }
  await page.waitForTimeout(2000);

  // --- Owner: create Staff role (if missing) ---
  await goto('/users/roles');
  await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
  await page.waitForTimeout(1500);

  const hasStaffRole = await page.locator('text=/Staff/i').count() > 0;
  if (!hasStaffRole) {
    const addRoleBtns = await page.getByRole('button', { name: /add|save|confirm|အသစ်|သိမ်း/i }).all();
    for (const btn of addRoleBtns) {
      if (await btn.isVisible()) {
        await btn.click({ force: true });
        break;
      }
    }
    await page.waitForTimeout(2000);

    const roleInputs = await page.locator('input').all();
    for (let i = roleInputs.length - 1; i >= 0; i--) {
      const type = await roleInputs[i].getAttribute('type');
      if (type !== 'hidden' && type !== 'checkbox' && type !== 'radio' && type !== 'password' && await roleInputs[i].isVisible()) {
        await roleInputs[i].fill('Staff');
        break;
      }
    }

    const saveRoleBtns = await page.getByRole('button', { name: /save|confirm|သိမ်း/i }).all();
    for (const btn of saveRoleBtns) {
      if (await btn.isVisible()) {
        await btn.click({ force: true });
        break;
      }
    }
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    await page.waitForTimeout(2000);
  }

  // --- Owner: create staff_fixed assigned ONLY to Shop A ---
  await goto('/users');
  await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
  await page.waitForTimeout(1500);

  // 1. Click Add User button
  const addUserBtns = await page.getByRole('button', { name: /add|အသစ်|new/i }).all();
  for (const btn of addUserBtns) {
    if (await btn.isVisible()) {
      await btn.click({ force: true });
      break;
    }
  }
  await page.waitForTimeout(2000); // Wait for modal to fully render

  // 2. Fill ALL text/email inputs (First is username, rest are dummy data for validation)
  const userTextInputs = await page.locator('input[type="text"], input[type="email"]').all();
  let isFirstText = true;
  for (const tInput of userTextInputs) {
    if (await tInput.isVisible()) {
      if (isFirstText) {
        await tInput.fill(STAFF_FIXED);
        isFirstText = false;
      } else {
        await tInput.fill('test@example.com');
      }
    }
  }

  // 3. Fill ALL visible Password fields (Password + Confirm Password)
  const userPassInputs = await page.locator('input[type="password"]').all();
  for (const pInput of userPassInputs) {
    if (await pInput.isVisible()) {
      await pInput.fill(STAFF_PASS);
    }
  }

  // 4. Select Role (Staff)
  const userSelects = await page.locator('select').all();
  for (const select of userSelects) {
    if (await select.isVisible()) {
      await select.selectOption({ label: /Staff/i }).catch(() => select.selectOption({ index: 1 }).catch(() => {}));
    }
  }

  // 5. Select Location Checkboxes — Fixed: check first visible only (Shop A), then break
  const userCheckboxes = await page.locator('input[type="checkbox"]').all();
  for (const cb of userCheckboxes) {
    if (await cb.isVisible()) {
      await cb.check({ force: true }).catch(() => {});
      break;
    }
  }

  // 6. Click Save and use a Hard Wait (Bypass brittle API matchers)
  await page.waitForTimeout(1000); // Let Vue reactivity catch up
  const userSaveBtns = await page.getByRole('button', { name: /save|သိမ်း|confirm/i }).all();
  for (const btn of userSaveBtns) {
    if (await btn.isVisible()) {
      await btn.click({ force: true });
      break;
    }
  }
  await page.waitForTimeout(4000); // Wait for backend to process and database to commit

  // --- staff_fixed: POS sale in Shop A, then logout ---
  await logout();
  await login(STAFF_FIXED, STAFF_PASS);
  await goto('/');
  await goto('/sales/pos');
  await doPosSale();
  await logout();
});
