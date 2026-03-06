# simulations/machinery_shop

Screenshots from **simulate_machinery_shop.js** (7-day Heavy Machinery & Electronic Shop simulation).

## Output files

| File        | Description                          |
|------------|--------------------------------------|
| `1.png` … `7.png` | Dashboard after each day's orders |
| `3_insight.png`   | AI Insight card on day 3        |
| `7_insight.png`   | AI Insight card on day 7        |

## How to run

From project root (`yp_posf`):

```bash
# Install Playwright (once)
npm install playwright
npx playwright install chromium
```

**တစ်ခါတည်း (Frontend ကိုယ်တိုင် စတင် + Simulation ပြေး):**

```bash
# Backend (Django) ကို သပ်သပ် ဖွင့်ထားပါ။ ပြီးရင်:
npm run simulate:machinery:full
# သို့
node run_machinery_sim.js
```

(Frontend ဖွင့်ပြီးသား ဆိုရင် ဒီလို ပြေးပါ: `node simulate_machinery_shop.js` သို့ `npm run simulate:machinery`)

This folder is created automatically when the script runs; screenshots are written here.
