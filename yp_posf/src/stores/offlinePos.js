/**
 * Offline-first POS: Pinia store + auto sync.
 * - Online: products ကို API ကနေ အလိုအလျောက် လွန်းပြီး IndexedDB သိမ်း။
 * - Offline: products က IndexedDB ကနေ သုံး၊ sale တွေကို queue ထဲ ထည့်။
 * - Online ပြန်ရှိရင် pending sales ကို အလိုအလျောက် POST လုပ်၊ products ပြန် လွန်းမယ်။
 */
import { defineStore } from 'pinia'
import api from '@/services/api'
import { posDb } from '@/db/posDb'
import { useAuthStore } from '@/stores/auth'

// api service က baseURL: '/api/' သတ်မှတ်ထားတယ်
const PRODUCTS_API = 'staff/items/'
const SALES_REQUEST_API = 'sales/request/'

/** Online ဖြစ်နေချိန် product list ကို ဒီကြာချိန်ပြန် လွန်းမယ် (ms) */
const AUTO_REFRESH_INTERVAL_MS = 2 * 60 * 1000 // 2 မိနစ်

export const useOfflinePosStore = defineStore('offlinePos', {
  state: () => ({
    products: [],
    isOnline: typeof navigator !== 'undefined' ? navigator.onLine : true,
    syncStatus: 'idle',
    pendingCount: 0,
    syncError: null,
    /** Sync progress: X of Y (Task F recommendation) */
    syncProgress: { current: 0, total: 0 },
    /** နောက်ဆုံး sync မှတ်တမ်း (debug / sync history) */
    syncHistory: [],
    /** နောက်ဆုံး sync/refresh လုပ်ခဲ့သည့် အချိန် (UI ပြရန်) */
    lastSyncedAt: null,
    _refreshTimerId: null,
    _boundHandlers: null,
  }),

  getters: {
    productsForPos: (state) => state.products,
    isOffline: (state) => !state.isOnline,
    hasPendingSales: (state) => state.pendingCount > 0,
    isSyncing: (state) => state.syncStatus === 'syncing',
    /** "3 of 5 synced" style text */
    syncProgressText: (state) =>
      state.syncProgress.total > 0
        ? `${state.syncProgress.current} of ${state.syncProgress.total} synced`
        : '',
  },

  actions: {
    /** Set online status (call when navigator.onLine changes or after fetch). */
    setOnline(value) {
      this.isOnline = !!value
    },

    /** Load products from IndexedDB into state (for offline use). */
    async loadProductsFromCache() {
      try {
        // Ensure database is open
        if (!posDb.isOpen()) {
          await posDb.open()
        }
        const list = await posDb.products.toArray()
        this.products = list
        return list
      } catch (e) {
        console.error('[offlinePos] loadProductsFromCache failed', e)
        this.products = []
        this.syncError = 'Cache read failed. Go online to refresh.'
        return []
      }
    },

    /** When online: fetch products from API and save to IndexedDB. အလိုအလျောက် lastSyncedAt update. */
    async fetchProductsAndCache() {
      if (typeof window === 'undefined') return this.products
      if (!useAuthStore().token) {
        await this.loadProductsFromCache()
        return this.products
      }
      try {
        // api service က auto token injection လုပ်ပေးတယ် (support with/without trailing slash to avoid 404)
        let res
        try {
          res = await api.get(PRODUCTS_API)
        } catch (e) {
          if (e.response?.status === 404 && PRODUCTS_API.endsWith('/')) {
            res = await api.get(PRODUCTS_API.slice(0, -1))
          } else {
            throw e
          }
        }
        const data = res.data
        const list = Array.isArray(data) ? data : (data?.results ?? [])
        const withUpdated = list.map((p) => ({ ...p, updated_at: Date.now() }))
        await posDb.products.clear()
        await posDb.products.bulkPut(withUpdated)
        this.products = withUpdated
        this.setOnline(true)
        this.syncError = null
        this.lastSyncedAt = Date.now()
        return this.products
      } catch (e) {
        if (e.response?.status === 401) {
          useAuthStore().$patch({ token: null })
          try { localStorage.removeItem('access_token') } catch (_) {}
          await this.loadProductsFromCache()
          return this.products
        }
        console.warn('[offlinePos] fetchProductsAndCache failed', e)
        this.setOnline(false)
        await this.loadProductsFromCache()
        return this.products
      }
    },

    /**
     * Ensure products are available: if online, fetch and cache; else load from IndexedDB.
     * Call this when entering POS (e.g. SalesRequest onMounted).
     */
    async ensureProducts() {
      if (typeof navigator !== 'undefined' && navigator.onLine) {
        return this.fetchProductsAndCache()
      }
      return this.loadProductsFromCache()
    },

    /** Get current pending count from IndexedDB (call after queue or sync). */
    async refreshPendingCount() {
      try {
        this.pendingCount = await posDb.pending_sales.count()
      } catch {
        this.pendingCount = 0
      }
    },

    /**
     * Queue a sale locally (when offline). Payload same as API: { customer, discount_amount, sale_items }.
     */
    async queuePendingSale(payload) {
      try {
        await posDb.pending_sales.add({
          payload,
          created_at: Date.now(),
        })
        await this.refreshPendingCount()
        return true
      } catch (e) {
        console.error('[offlinePos] queuePendingSale failed', e)
        return false
      }
    },

    /**
     * Submit sale: if online, POST to API; if offline, queue and show pending.
     * Returns { ok: boolean, offline?: boolean, invoice_number?: string, error?: string }
     */
    async submitSale(payload) {
      if (typeof navigator !== 'undefined' && navigator.onLine) {
        try {
          // api service က auto token injection လုပ်ပေးတယ်
          const { data } = await api.post(SALES_REQUEST_API, payload)
          return { ok: true, invoice_number: data.invoice_number || data.id, id: data.id, sale_id: data.id }
        } catch (e) {
          const msg = e.response?.data ? JSON.stringify(e.response.data) : e.message
          return { ok: false, error: msg }
        }
      }
      const queued = await this.queuePendingSale(payload)
      return { ok: queued, offline: true }
    },

    /**
     * Sync pending sales to the server. Call on window.ononline or manually.
     * POSTs each pending sale in order; removes from IndexedDB on success.
     * Updates syncProgress (X of Y) and syncHistory (Task F recommendation).
     */
    async syncPendingSales() {
      if (!useAuthStore().token) {
        this.syncStatus = 'idle'
        return { synced: 0, failed: 0 }
      }
      this.syncStatus = 'syncing'
      this.syncError = null
      this.syncProgress = { current: 0, total: 0 }
      try {
        if (typeof window === 'undefined' || !posDb?.pending_sales) {
          this.syncStatus = 'idle'
          return { synced: 0, failed: 0 }
        }
        const pending = await posDb.pending_sales.orderBy('created_at').toArray()
        const total = pending.length
        this.syncProgress = { current: 0, total }
        let failed = 0
        let synced = 0
        for (let i = 0; i < pending.length; i++) {
          const row = pending[i]
          try {
            if (!row?.payload) continue
            await api.post(SALES_REQUEST_API, row.payload)
            await posDb.pending_sales.delete(row.localId)
            synced++
          } catch (e) {
            failed++
            console.warn('[offlinePos] sync failed for pending sale', row.localId, e)
          }
          this.syncProgress = { current: i + 1, total }
        }
        await this.refreshPendingCount()
        const entry = {
          at: Date.now(),
          synced,
          failed,
          total,
        }
        this.syncHistory = [entry, ...(this.syncHistory || []).slice(0, 19)]
        if (failed > 0) {
          this.syncError = `${failed} sale(s) failed to sync`
          this.syncStatus = 'error'
        } else {
          this.syncStatus = 'idle'
          this.lastSyncedAt = Date.now()
        }
        this.syncProgress = { current: 0, total: 0 }
        return { synced, failed }
      } catch (e) {
        this.syncError = e?.message || 'Sync failed'
        this.syncStatus = 'error'
        this.syncProgress = { current: 0, total: 0 }
        return { synced: 0, failed: -1 }
      }
    },

    _startAutoRefresh() {
      if (this._refreshTimerId) return
      this._refreshTimerId = setInterval(() => {
        if (navigator.onLine) this.fetchProductsAndCache().catch(() => {})
      }, AUTO_REFRESH_INTERVAL_MS)
    },

    _stopAutoRefresh() {
      if (this._refreshTimerId) {
        clearInterval(this._refreshTimerId)
        this._refreshTimerId = null
      }
    },

    /** Tab ပြန်ဖွင့်ချိန် (သို့) online ဖြစ်ချိန် ဒေတာ အလိုအလျောက် လွန်းမယ်။ */
    _onVisibleOrOnline() {
      if (typeof document === 'undefined' || document.visibilityState !== 'visible') return
      if (navigator.onLine) {
        this.fetchProductsAndCache().catch(() => {})
      }
    },

    /**
     * Global listener များ ချိတ်ပြီး အလိုအလျောက် sync စတင်။
     * - online: pending sales sync + products လွန်းမယ်၊ auto-refresh timer စမယ်။
     * - offline: cache ကနေ products သုံးမယ်၊ timer ရပ်မယ်။
     * - visibilitychange: tab ပြန်ဖွင့်ရင် (online ဆိုရင်) products ပြန် လွန်းမယ်။
     */
    initOfflineSync() {
      if (typeof window === 'undefined') return
      if (this._boundHandlers) return

      const handleOnline = async () => {
        this.setOnline(true)
        this._startAutoRefresh()
        await this.syncPendingSales()
      }

      const handleOffline = () => {
        this.setOnline(false)
        this._stopAutoRefresh()
        this.loadProductsFromCache().catch(() => {})
      }

      const handleVisibility = () => this._onVisibleOrOnline()

      window.addEventListener('online', handleOnline)
      window.addEventListener('offline', handleOffline)
      document.addEventListener('visibilitychange', handleVisibility)
      this._boundHandlers = { handleOnline, handleOffline, handleVisibility }

      this.setOnline(navigator.onLine)
      this.refreshPendingCount()

      const hasToken = !!useAuthStore().token
      if (navigator.onLine && hasToken) {
        this._startAutoRefresh()
        this.fetchProductsAndCache().then(() => {})
        this.syncPendingSales().then(() => {})
      } else {
        this.loadProductsFromCache().then(() => {})
      }
    },
  },
})
