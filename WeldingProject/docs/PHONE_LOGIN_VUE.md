# Phone Number Login – Vue Frontend Reference

Backend exposes **phone + password** login. Use this doc to implement the Login UI and auth state in your Vue app.

## API

- **Endpoint:** `POST /api/core/auth/phone-login/`
- **Body:**
  ```json
  {
    "phone_number": "09xxxxxxxx",
    "country_code": "+95",
    "password": "your_password"
  }
  ```
- **Country code:** Default `+95` (Myanmar). Optional dropdown for other codes later.

### Success (200)

```json
{
  "access": "eyJ...",
  "refresh": "eyJ...",
  "user": {
    "id": 1,
    "username": "u959xxxxxxxx",
    "phone_number": "959xxxxxxxx",
    "first_name": "...",
    "last_name": "...",
    "role": "staff",
    "requires_password_change": false
  },
  "outlet": {
    "id": 1,
    "name": "Main Branch",
    "code": "MB"
  }
}
```

- If user has no primary outlet, `outlet` can be `null`. Use `user` and `outlet` for session/outlet filtering so staff see the right shop data.

### Error responses

- **400** – Validation (e.g. invalid Myanmar phone, missing phone/password): `{ "detail": "..." }`
- **401** – Wrong password: `{ "detail": "Invalid credentials." }` (failed attempt counted)
- **403** – Locked (5 failed attempts): `{ "detail": "Too many failed attempts...", "locked_until": "2025-01-01T12:00:00Z" }`

---

## Vue Login Screen

- **Fields:** Country code (dropdown), Phone number, Password.
- **Country code:** Default `+95`. Options example: `[{ value: '+95', label: 'Myanmar (+95)' }, ...]`.
- **Phone:** Input for national number (e.g. `09xxxxxxxx`). Send as-is; backend normalizes.
- **Password:** Normal password input.
- **Submit:** `POST /api/core/auth/phone-login/` with `{ phone_number, country_code, password }`.

### Example (Composition API + fetch)

```vue
<template>
  <form @submit.prevent="login">
    <div>
      <label>Country Code</label>
      <select v-model="countryCode">
        <option value="+95">Myanmar (+95)</option>
        <!-- add more if needed -->
      </select>
    </div>
    <div>
      <label>Phone Number</label>
      <input v-model="phoneNumber" type="tel" placeholder="09xxxxxxxx" required />
    </div>
    <div>
      <label>Password</label>
      <input v-model="password" type="password" required />
    </div>
    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="lockedUntil">Account locked until {{ lockedUntil }}.</p>
    <button type="submit" :disabled="loading">Login</button>
  </form>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth' // or your auth store path

const authStore = useAuthStore()
const phoneNumber = ref('')
const countryCode = ref('+95')
const password = ref('')
const loading = ref(false)
const error = ref('')
const lockedUntil = ref('')

const apiBase = '/api/core' // or your base URL

async function login() {
  error.value = ''
  lockedUntil.value = ''
  loading.value = true
  try {
    const res = await fetch(`${apiBase}/auth/phone-login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        phone_number: phoneNumber.value.trim(),
        country_code: countryCode.value,
        password: password.value,
      }),
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) {
      if (res.status === 403 && data.locked_until) {
        lockedUntil.value = new Date(data.locked_until).toLocaleString()
      }
      error.value = data.detail || 'Login failed.'
      return
    }
    // Success: store tokens and user/outlet
    authStore.setAuth({
      access: data.access,
      refresh: data.refresh,
      user: data.user,
      outlet: data.outlet,
    })
    // Redirect to dashboard or, if required, change-password page
    if (data.user?.requires_password_change) {
      // navigate to /change-password
      return
    }
    // navigate to /dashboard or home
  } finally {
    loading.value = false
  }
}
</script>
```

---

## Auth store (session + outlet)

After a successful phone login, persist and use:

- **access** – JWT for `Authorization: Bearer <access>`.
- **refresh** – For refreshing the access token when it expires.
- **user** – Current user (id, username, phone_number, role, requires_password_change, etc.).
- **outlet** – `{ id, name, code }` or `null`; use for outlet-scoped data so staff see the right shop.

Example (Pinia-style):

```js
// stores/auth.js (or auth.ts)
export function useAuthStore() {
  const access = ref(localStorage.getItem('access') || '')
  const refresh = ref(localStorage.getItem('refresh') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const outlet = ref(JSON.parse(localStorage.getItem('outlet') || 'null'))

  function setAuth({ access: a, refresh: r, user: u, outlet: o }) {
    access.value = a
    refresh.value = r
    user.value = u
    outlet.value = o
    if (a) localStorage.setItem('access', a)
    if (r) localStorage.setItem('refresh', r)
    if (u) localStorage.setItem('user', JSON.stringify(u))
    localStorage.setItem('outlet', o ? JSON.stringify(o) : 'null')
  }

  function logout() {
    access.value = ''
    refresh.value = ''
    user.value = null
    outlet.value = null
    ;['access', 'refresh', 'user', 'outlet'].forEach(k => localStorage.removeItem(k))
  }

  return { access, refresh, user, outlet, setAuth, logout }
}
```

Use **outlet.id** (or your existing outlet context) in API calls so the backend returns data for the correct shop.

---

## First login / change password

If `user.requires_password_change === true`, redirect to your change-password page. Your app likely already has a “reset password” or “set password” flow; use the same endpoint with the token (e.g. from reset link or first-login flow). After a successful password change, the backend sets `requires_password_change = False` so the next login will not redirect to change-password.

---

## Security (backend)

- **5 failed attempts** per phone number → account locked for **15 minutes**.
- Lockout is per normalized phone (e.g. 09... and +959... map to the same record).
- Outlet is still tied to the user session via `user` and `outlet` in the login response; use them for outlet-scoped UI and API calls.
