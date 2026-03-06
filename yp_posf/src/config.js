/**
 * API URL - Use relative /api/ so Register and API work from same origin (Django-served /app/ or dev).
 * Set VITE_API_URL for custom proxy (e.g. Nginx).
 * For Capacitor mobile app: Use backend URL (localhost for dev, hosted URL for production)
 * For Expo Go app: Use backend URL from window.EXPO_API_URL or environment
 *
 * Loyverse-Style Standalone Hardware POS (MM Edition). Single-shop only. License Key Activation is the sole gatekeeper (no SaaS, no multi-tenancy, no subscriptions).
 * EXE vs Server: VITE_BUILD_TARGET=exe | server. License via backend (license.lic or DB).
 */
const isCapacitor = typeof window !== 'undefined' && window.Capacitor !== undefined
const isExpo = typeof window !== 'undefined' && window.EXPO_READY === true
const env = import.meta.env.VITE_API_URL || ''

// Mobile app: Use backend URL from capacitor.config.ts server.url or Expo config or environment
// Web: Use relative /api/ or proxy
let API_BASE = ''
let API_URL = '/api/'

if (isCapacitor) {
  // Capacitor mobile app - use backend URL
  const backendUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  API_BASE = backendUrl
  API_URL = `${backendUrl}/api/`
} else if (isExpo) {
  // Expo Go app - use API URL from Expo WebView injection
  const expoApiUrl = typeof window !== 'undefined' && window.EXPO_API_URL 
    ? window.EXPO_API_URL 
    : (import.meta.env.VITE_API_URL || 'http://localhost:8000/api')
  API_BASE = expoApiUrl.replace('/api', '')
  API_URL = expoApiUrl.endsWith('/') ? expoApiUrl : expoApiUrl + '/'
} else if (env) {
  // Custom API URL set (e.g. VITE_API_URL=/api for Docker → API_URL=/api/)
  const base = env.endsWith('/') ? env.slice(0, -1) : env
  API_BASE = base
  // If env is already /api or ends with /api, use as-is; else append /api/
  API_URL = (base === '/api' || base.endsWith('/api')) ? `${base}/` : `${base}/api/`
} else {
  // Default: relative /api/ for web
  API_BASE = typeof window !== 'undefined' ? '' : 'http://127.0.0.1:8000'
  API_URL = '/api/'
}

const BUILD_TARGET = import.meta.env.VITE_BUILD_TARGET || 'server'
const isExeBuild = BUILD_TARGET === 'exe'

/**
 * Fix media/image URLs that point to http(s)://localhost/ (no port) → ERR_CONNECTION_REFUSED.
 * Rewrites to API_BASE when set (e.g. http://localhost:8000) so the browser loads from the backend.
 */
function mediaUrl(url) {
  if (!url || typeof url !== 'string') return url
  const match = url.match(/^(https?:\/\/)localhost(\/.*)$/)
  if (match && API_BASE) return (API_BASE.replace(/\/$/, '') + match[2]) || url
  return url
}

export { API_BASE, API_URL, isExeBuild, BUILD_TARGET, mediaUrl }
