# Standalone Cloud POS – Spec & Docker

## 1. Single-Shop, No SaaS

- **Single-shop database** – No tenant filters, subscription tiers, or multi-shop switching.
- **Gatekeeper:** **License Key Activation** only (see `license/services.py` and `/license-activate`).
- **Config:** `yp_posf/src/config.js` documents standalone behaviour (no SaaS tiers, no tenant/subdomain).

## 2. Docker Frontend Build (Node 22 LTS)

### Frontend-only image (`yp_posf/Dockerfile`)

- **Base:** `node:22-bullseye` (Stage 1), then `nginx:stable-alpine` (Stage 2).
- **Memory:** `ENV NODE_OPTIONS="--max-old-space-size=4096"`.
- **Install:** `npm cache clean --force` then `npm install --legacy-peer-deps`.
- **Pre-build diagnostic:** `RUN ls -la src/` and `RUN ls -la public/` to verify files before build.
- **Build:** `npm run build`; output → `/app/dist` (Stage 1) → copied to Nginx `/usr/share/nginx/html`.

### Combined backend image (`WeldingProject/Dockerfile`)

- **Stage 1 (frontend):** Same as above – Node 22 bullseye, 4096 MB, cache clean, `--legacy-peer-deps`, `ls -la src/` and `ls -la public/`, then `npm run build`.
- **Stage 2 (Django):** Python 3.11-slim; frontend build is copied to **`/app/static_frontend`** so Django’s `STATICFILES_DIRS` and SPA views serve it (no Whitenoise required; Django static + custom SPA routes).
- **Build from repo root:**
  ```bash
  docker compose build backend --no-cache --progress=plain
  ```
- **On build failure:** Full log is shown (no build.log redirect). Check Vite/npm errors in the Docker output.

### Vite/Django asset serving (avoid 404 for JS/CSS)

- **Vite:** `vite.config.js` has `base: process.env.VITE_BASE || '/'`, `build.outDir: 'dist'`, `build.assetsDir: 'assets'`. Built `index.html` uses absolute asset URLs (e.g. `/app/assets/Register-XXX.js` when `VITE_BASE=/app/`).
- **Django:** `STATIC_FRONTEND_DIR` = `static_frontend` (same as Docker copy target). Routes: `path('assets/<path:path>', serve_frontend_assets)` for `/assets/*`, and `path('app/<path:path>', vue_spa_view)` for `/app/*` (including `/app/assets/*`). Catch-all at the end serves `index.html` for any other non-API path.
- **Docker:** `COPY --from=frontend /fe/dist /app/static_frontend` so `index.html` and `assets/` live where Django expects.

## 3. Standalone Behaviour

- **Offline:** IndexedDB + sync in `offlinePos` store; POS supports offline sales and sync when online.
- **UI:** 25px fonts, 80px buttons (Myanmar senior-friendly).
- **Industry:** Pharmacy, Solar/AC, Phone/PC, Hardware, General – local setting only (Settings → business type). License key is the only activation gate.

## 4. Code Integrity (Linux/Docker-safe)

- **Case sensitivity:** Imports in `frontend/src/` were scanned; all paths match actual filenames (e.g. `@/views/Settings.vue`, `./settings/PaymentMethodSettings.vue`). No case-only fixes required.
- **Imports:** No broken or missing imports that would cause “Module not found” or minification Exit Code 1. Unused imports (if any) do not block the build.

## 5. QC & Cleanup

- **CSS:** Minimal animations in `.pos-layout` (short transitions only; no heavy transforms).
- **Container:** Healthcheck `start_period=40s`; aim for app ready in &lt;60s after container start.
- **Build failure:** Run with `--progress=plain` and check the Docker output for the real Vite/npm error after the `ls -la` diagnostic lines.
