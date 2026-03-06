# Routing & API Connections (Loyverse-style)

## Normal usage (ပုံမှန်လုပ်နေကြအတိုင်း)

| URL | Purpose |
|-----|--------|
| **localhost:5173** (dev) or **localhost** (Docker) or **localhost:8000/app/** | **Vue app – single entry.** Do everything from here: Login, Register, POS, Items, Reports, Settings. No need to open Django admin. |
| **localhost:8000/** | Django root → redirects to `/app/` (Vue SPA). |
| **localhost:8000/api/** | Backend API. Used by Vue via proxy (dev) or same origin (Docker/prod). |
| **localhost:8000/admin/** | Django admin → redirects to `/app/`. (Use Vue app only.) |

## Dev (npm run dev)

- Run **Vue** at **http://localhost:5173**. All UI and navigation stay in Vue.
- **API**: Requests to `/api/*` are proxied to **http://127.0.0.1:8000** (see `vite.config.js`).
- Start Django: `python manage.py runserver` (or Docker backend on 8000). No need to open 8000 in the browser for normal use.

## Docker / Production

- **http://localhost/** (port 80): Nginx serves Vue at `/app/` and proxies `/api/` to backend.
- **http://localhost:8000**: Backend only; use **http://localhost/app/** for the app.

## Connection checks (404, 301, 500, 405)

| Check | Expected |
|-------|----------|
| **GET /** or **GET /app/** | 200 (HTML) or 302 → /app/. |
| **GET /app/assets/*.js** | 200 (no 404). Build with `VITE_BASE=/app/` when serving at `/app/`. |
| **POST /api/core/auth/login/** | 200 + `{ access, refresh, user, outlet }` or 401 with `detail`. |
| **POST /api/token/** | 200 + `{ access, refresh }` with `username`+`password` or `login` (phone/email)+`password`. |
| **GET /api/core/me/** | 200 with valid Bearer token; 401 without. |
| **301** | Only for redirects (e.g. `/` → `/app/`, `/login/` → `/app/login`). |
| **405** | Only if method not allowed (e.g. GET on POST-only endpoint). |

## Login

- **Vue** uses **POST /api/core/auth/login/** with `{ login, password, country_code }` (phone or email in `login`).
- **POST /api/token/** also accepts `login` (phone/email) + `password` and returns JWT so Swagger/Postman or any client using `/api/token/` work.

## Loyverse UI

- **Background**: White / light gray (`#ffffff`, `#f4f4f4`).
- **Text**: Black / dark gray (`#1a1a1a`).
- **Primary buttons**: Loyverse blue (`#1078D1`).
- **Secondary buttons**: White with border; hover blue.
