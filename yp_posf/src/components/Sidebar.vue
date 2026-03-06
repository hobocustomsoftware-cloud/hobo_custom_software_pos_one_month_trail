<template>
  <!-- Mobile backdrop: below sidebar so sidebar stays on top -->
  <div
    v-show="mobileOpen"
    class="fixed inset-0 bg-black/50 z-[55] lg:hidden transition-opacity backdrop-blur-sm"
    aria-hidden="true"
    @click="$emit('update:mobileOpen', false)"
  />
  <!-- Glass Sidebar: fixed on mobile (drawer); in-flow on desktop (lg:relative) so main content shrinks when expanded -->
  <aside
    class="sidebar-rail fixed inset-y-0 left-0 z-[60] flex flex-col font-sans min-h-screen lg:min-h-0 transition-all duration-[400ms] ease-[cubic-bezier(0.4,0,0.2,1)] w-72 max-w-[85vw] glass-surface border-r border-[var(--surface-border)] lg:relative lg:z-auto lg:w-full lg:max-w-none lg:translate-x-0 lg:shadow-2xl lg:shadow-black/50"
    :class="[
      mobileOpen ? 'translate-x-0' : '-translate-x-full',
    ]"
    @mouseenter="onSidebarMouseEnter"
    @mouseleave="onSidebarMouseLeave"
  >
    <!-- Header: logo + shop name + collapse toggle (desktop) -->
    <div class="flex items-center justify-between gap-3 p-4 lg:justify-between lg:px-3 flex-shrink-0">
      <div class="flex items-center gap-3 min-w-0">
        <div class="p-1.5 rounded-xl bg-white/10 border border-white/20 flex items-center justify-center w-10 h-10 min-w-[2.5rem] min-h-[2.5rem] overflow-hidden shrink-0">
          <img v-show="!logoError && shopLogo" :src="shopLogo" alt="Logo" class="w-10 h-10 object-contain" @error="logoError=true" />
          <img v-show="!logoError && !shopLogo" :src="defaultLogo" alt="Logo" class="w-10 h-10 object-contain" @error="logoError=true" />
          <span v-show="logoError" class="text-sm font-bold text-white/80">{{ shopName.slice(0,4) }}</span>
        </div>
        <span
          class="text-lg font-extrabold tracking-tight text-white truncate"
          :class="showLabels ? 'lg:inline' : 'lg:hidden'"
        >{{ shopName }}</span>
      </div>
      <div class="flex items-center gap-1">
        <button
          v-if="showLabels"
          type="button"
          class="hidden lg:flex p-2 rounded-xl text-white/60 hover:bg-white/10 transition-all"
          aria-label="Collapse sidebar"
          @click="$emit('update:collapsed', true)"
        >
          <ChevronLeft class="w-5 h-5" />
        </button>
        <button
          v-if="!showLabels"
          type="button"
          class="hidden lg:flex p-2 rounded-xl text-white/60 hover:bg-white/10 transition-all"
          aria-label="Expand sidebar"
          @click="$emit('update:collapsed', false)"
        >
          <ChevronRight class="w-5 h-5" />
        </button>
        <button
          type="button"
          class="lg:hidden p-2 rounded-xl text-white/60 hover:bg-white/10"
          aria-label="Close menu"
          @click="$emit('update:mobileOpen', false)"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
        </button>
      </div>
    </div>

    <!-- USD Exchange Rate Display (Glassmorphism) -->
    <div class="px-3 pb-3 flex-shrink-0">
      <div class="glass-card p-3 rounded-xl border border-[var(--surface-border)] glow-effect">
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2 min-w-0 flex-1">
            <span class="text-lg">💱</span>
            <div class="min-w-0 flex-1" :class="showLabels ? 'lg:block' : 'lg:hidden'">
              <div class="flex items-center gap-2">
                <div class="text-xs font-bold text-white/70 uppercase tracking-wider">USD Rate</div>
                <!-- Live Exchange Rate Badge: AUTO (Green) or MANUAL (Red) -->
                <span
                  class="px-1.5 py-0.5 rounded text-xs font-black uppercase tracking-wider"
                  :class="isAutoSync ? 'bg-green-500/20 text-green-400 glow-green' : 'bg-red-500/20 text-red-400 glow-red'"
                >
                  {{ isAutoSync ? 'AUTO' : 'MANUAL' }}
                </span>
              </div>
              <div class="text-sm font-black text-white truncate" :title="!exchangeRate.usdExchangeRate ? 'Click gear to sync or set manual rate' : ''">
                {{ usdRateDisplay }}
              </div>
            </div>
            <div class="lg:hidden">
              <div class="flex items-center gap-1">
                <div class="text-xs font-bold text-white/70 uppercase">USD</div>
                <span
                  class="px-1 py-0.5 rounded text-xs font-black uppercase"
                  :class="isAutoSync ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'"
                >
                  {{ isAutoSync ? 'AUTO' : 'MAN' }}
                </span>
              </div>
              <div class="text-sm font-black text-white">{{ usdRateDisplay }}</div>
            </div>
          </div>
          <div class="flex items-center gap-1">
            <button
              @click="openRateManagement"
              class="p-1.5 rounded-lg bg-white/10 hover:bg-white/20 transition-all interactive"
              title="Manage Exchange Rate"
            >
              <svg class="w-4 h-4 text-white/80" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </button>
            <button
              @click="syncExchangeRate"
              :disabled="syncingRate"
              class="p-1.5 rounded-lg bg-white/10 hover:bg-white/20 transition-all interactive disabled:opacity-50"
              :title="syncingRate ? 'Syncing...' : 'Sync Exchange Rate'"
            >
              <svg
                v-if="syncingRate"
                class="w-4 h-4 text-white animate-spin"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <svg
                v-else
                class="w-4 h-4 text-white/80"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          </div>
        </div>
        <div v-if="rateLastUpdated" class="text-xs text-white/50 mt-1" :class="showLabels ? 'lg:block' : 'lg:hidden'">
          Updated: {{ rateLastUpdated }}
        </div>
      </div>
    </div>

    <!-- Rate Management Modal -->
    <RateManagementModal
      :is-open="showRateManagementModal"
      @update:is-open="showRateManagementModal = $event"
      @saved="handleRateSettingsSaved"
    />

    <div class="flex-1 px-2 lg:px-2 min-h-0">
      <!-- General -->
      <div class="mb-4 lg:mb-1">
        <p class="px-2 mb-2 text-xs font-black text-white/60 uppercase tracking-widest" :class="showLabels ? 'lg:block' : 'lg:hidden'">General</p>
        <nav class="space-y-0.5 lg:space-y-1">
          <RouterLink
            v-for="item in generalItems"
            :key="item.path"
            :to="item.path"
            :title="item.name"
            class="sidebar-link flex items-center gap-3 p-2.5 rounded-xl font-bold transition-all duration-300 hover:bg-white/10 text-white/70"
            :class="showLabels ? 'lg:justify-start' : 'lg:justify-center'"
            exact-active-class="sidebar-link-active"
          >
            <component :is="item.icon" class="w-5 h-5 lg:w-6 lg:h-6 shrink-0" :class="$route.path === item.path ? 'text-white' : 'text-white/50'" />
            <span class="text-base truncate" :class="showLabels ? 'lg:inline' : 'lg:hidden'">{{ item.name }}</span>
          </RouterLink>
        </nav>
      </div>

      <!-- Management (desktop: flat icons; mobile: expandable) -->
      <div class="mb-4 lg:mb-1">
        <p class="px-2 mb-2 text-xs font-black text-white/60 uppercase tracking-widest" :class="showLabels ? 'lg:block' : 'lg:hidden'">Management</p>
        <nav class="space-y-0.5 lg:space-y-1">
          <template v-for="item in managementItems" :key="item.path">
            <template v-if="item.path === '/users'">
              <!-- Mobile: expandable -->
              <div class="lg:hidden space-y-0">
                <button
                  type="button"
                  @click="userManagementOpen = !userManagementOpen"
                  class="w-full flex items-center justify-between gap-3 p-2.5 rounded-xl font-bold transition-all hover:bg-white/10 text-white/70"
                >
                  <div class="flex items-center gap-3">
                    <component :is="item.icon" class="w-5 h-5 text-white/50" />
                    <span class="text-base">User Management</span>
                  </div>
                  <ChevronDown class="w-4 h-4 text-white/50" :class="userManagementOpen ? 'rotate-180' : ''" />
                </button>
                <div v-show="userManagementOpen" class="pl-4 pt-0.5 pb-1 space-y-0.5 border-l-2 border-white/20 ml-5">
                  <RouterLink to="/users" class="flex items-center gap-2 py-2 pl-3 rounded-lg text-[12px] font-bold hover:bg-white/10 text-white/70" active-class="sidebar-link-active"><Users class="w-4 h-4" /><span>ဝန်ထမ်းများ</span></RouterLink>
                  <RouterLink to="/users/roles" class="flex items-center gap-2 py-2 pl-3 rounded-lg text-[12px] font-bold hover:bg-white/10 text-white/70" active-class="sidebar-link-active"><UserCog class="w-4 h-4" /><span>Role များ</span></RouterLink>
                </div>
              </div>
              <!-- Desktop: two icon links -->
              <RouterLink to="/users" title="ဝန်ထမ်းများ" class="hidden lg:flex items-center gap-3 p-2.5 rounded-xl font-bold transition-all duration-300 hover:bg-white/10 text-white/70" :class="[showLabels ? 'lg:justify-start' : 'lg:justify-center']" active-class="sidebar-link-active">
                <Users class="w-6 h-6 shrink-0" :class="$route.path === '/users' && $route.path !== '/users/roles' ? 'text-white' : 'text-white/50'" />
                <span class="text-base truncate" :class="showLabels ? 'lg:inline' : 'lg:hidden'">ဝန်ထမ်းများ</span>
              </RouterLink>
              <RouterLink to="/users/roles" title="Role များ" class="hidden lg:flex items-center gap-3 p-2.5 rounded-xl font-bold transition-all duration-300 hover:bg-white/10 text-white/70" :class="[showLabels ? 'lg:justify-start' : 'lg:justify-center']" active-class="sidebar-link-active">
                <UserCog class="w-6 h-6 shrink-0" :class="$route.path === '/users/roles' ? 'text-white' : 'text-white/50'" />
                <span class="text-base truncate" :class="showLabels ? 'lg:inline' : 'lg:hidden'">Role များ</span>
              </RouterLink>
            </template>
            <RouterLink
              v-else
              :to="item.path"
              :title="item.name"
              class="sidebar-link flex items-center gap-3 p-2.5 rounded-xl font-bold transition-all duration-300 hover:bg-white/10 text-white/70"
              :class="showLabels ? 'lg:justify-start' : 'lg:justify-center'"
              exact-active-class="sidebar-link-active"
            >
              <component :is="item.icon" class="w-5 h-5 lg:w-6 lg:h-6 shrink-0" :class="$route.path === item.path ? 'text-white' : 'text-white/50'" />
              <span class="text-base truncate" :class="showLabels ? 'lg:inline' : 'lg:hidden'">{{ item.name }}</span>
            </RouterLink>
          </template>
        </nav>
      </div>

      <!-- Accounting: Expense + P&L (full feature list) -->
      <div v-if="accountingItems.length" class="mb-4 lg:mb-1">
        <p class="px-2 mb-2 text-xs font-black text-white/60 uppercase tracking-widest" :class="showLabels ? 'lg:block' : 'lg:hidden'">Accounting</p>
        <nav class="space-y-0.5 lg:space-y-1">
          <RouterLink
            v-for="item in accountingItems"
            :key="item.path"
            :to="item.path"
            :title="item.name"
            class="sidebar-link flex items-center gap-3 p-2.5 rounded-xl font-bold transition-all duration-300 hover:bg-white/10 text-white/70"
            :class="showLabels ? 'lg:justify-start' : 'lg:justify-center'"
            exact-active-class="sidebar-link-active"
          >
            <component :is="item.icon" class="w-5 h-5 lg:w-6 lg:h-6 shrink-0" :class="$route.path === item.path ? 'text-white' : 'text-white/50'" />
            <span class="text-base truncate" :class="showLabels ? 'lg:inline' : 'lg:hidden'">{{ item.name }}</span>
          </RouterLink>
        </nav>
      </div>

      <!-- Reports -->
      <div v-if="reportItems.length" class="mb-4 lg:mb-1">
        <p class="px-2 mb-2 text-xs font-black text-white/60 uppercase tracking-widest" :class="showLabels ? 'lg:block' : 'lg:hidden'">Reports & Analysis</p>
        <nav class="space-y-0.5 lg:space-y-1">
          <RouterLink
            v-for="item in reportItems"
            :key="item.path"
            :to="item.path"
            :title="item.name"
            class="sidebar-link flex items-center gap-3 p-2.5 rounded-xl font-bold transition-all duration-300 hover:bg-white/10 text-white/70"
            :class="showLabels ? 'lg:justify-start' : 'lg:justify-center'"
            exact-active-class="sidebar-link-active"
          >
            <component :is="item.icon" class="w-5 h-5 lg:w-6 lg:h-6 shrink-0" :class="$route.path === item.path ? 'text-white' : 'text-white/50'" />
            <span class="text-base truncate" :class="showLabels ? 'lg:inline' : 'lg:hidden'">{{ item.name }}</span>
          </RouterLink>
        </nav>
      </div>

      <!-- Public -->
      <div class="mb-4 lg:mb-1">
        <p class="px-2 mb-2 text-xs font-black text-white/60 uppercase tracking-widest" :class="showLabels ? 'lg:block' : 'lg:hidden'">Customer (Public)</p>
        <nav class="space-y-0.5 lg:space-y-1">
          <RouterLink
            v-for="item in publicItems"
            :key="item.path"
            :to="item.path"
            :title="item.name"
            class="sidebar-link flex items-center gap-3 p-2.5 rounded-xl font-bold transition-all duration-300 hover:bg-white/10 text-white/70"
            :class="showLabels ? 'lg:justify-start' : 'lg:justify-center'"
            exact-active-class="sidebar-link-active"
          >
            <component :is="item.icon" class="w-5 h-5 lg:w-6 lg:h-6 shrink-0" :class="$route.path === item.path ? 'text-white' : 'text-white/50'" />
            <span class="text-base truncate" :class="showLabels ? 'lg:inline' : 'lg:hidden'">{{ item.name }}</span>
          </RouterLink>
        </nav>
      </div>
    </div>

    <div class="p-2 border-t border-[var(--surface-border)] flex-shrink-0">
      <button
        @click="handleLogout"
        title="Logout"
        class="w-full flex items-center gap-2 p-2.5 rounded-xl text-red-300 font-black text-[11px] hover:bg-white/10 transition-all duration-300 uppercase tracking-wider"
        :class="showLabels ? 'lg:justify-start lg:px-3' : 'lg:justify-center'"
      >
        <LogOut class="w-5 h-5 lg:w-6 lg:h-6 shrink-0" />
        <span class="truncate" :class="showLabels ? 'lg:inline' : 'lg:hidden'">Logout Session</span>
      </button>
      <p class="text-xs font-bold text-white/50 text-center mt-2" :class="showLabels ? 'lg:block' : 'lg:hidden'">© {{ currentYear }} {{ shopName }}</p>
    </div>
  </aside>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getLoginPath } from '@/router'
import { useShopSettingsStore } from '@/stores/shopSettings'
import { useAuthStore } from '@/stores/auth'
import { useExchangeRateStore } from '@/stores/exchangeRate'
import { useFeatureTogglesStore } from '@/stores/featureToggles'
import api from '@/services/api'
import RateManagementModal from './RateManagementModal.vue'
import {
  LayoutDashboard,
  Box,
  ShoppingCart,
  Users,
  Tags,
  ArrowUpDown,
  Map,
  CheckCircle,
  History,
  ToolCase,
  BarChart3,
  FileText,
  Wrench,
  Shield,
  Settings,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  UserCog,
  DollarSign,
  TrendingUp,
  LogOut,
} from 'lucide-vue-next'

const props = defineProps({
  mobileOpen: { type: Boolean, default: false },
  collapsed: { type: Boolean, default: true },
})
const emit = defineEmits(['update:mobileOpen', 'update:collapsed', 'hover-start', 'hover-end'])

const sidebarHover = ref(false)

// Desktop: show labels when expanded (manual) or when mini + hover (parent column grows, no overlay)
const showLabels = computed(() => props.collapsed ? sidebarHover.value : true)

function onSidebarMouseEnter() {
  sidebarHover.value = true
  emit('hover-start')
}
function onSidebarMouseLeave() {
  sidebarHover.value = false
  emit('hover-end')
}

const base = import.meta.env.BASE_URL || '/'
const defaultLogo = base + 'logo.svg'
const logoError = ref(false)
const shopStore = useShopSettingsStore()
const shopLogo = computed(() => shopStore.logo_url)
const shopName = computed(() => shopStore.displayName)

const router = useRouter()
const authStore = useAuthStore()
const exchangeRate = useExchangeRateStore()
const featureToggles = useFeatureTogglesStore()
const syncingRate = ref(false)
const rateLastUpdated = ref(null)
const isAutoSync = ref(true)
const showRateManagementModal = ref(false)

const userManagementOpen = ref(
  ['/users', '/users/roles'].includes(router.currentRoute.value.path),
)
const currentYear = new Date().getFullYear()

const usdRateDisplay = computed(() => {
  const rate = exchangeRate.usdExchangeRate
  if (rate != null && Number(rate) > 0) {
    return Math.round(Number(rate) || 0).toLocaleString(undefined, { maximumFractionDigits: 0 }) + ' MMK'
  }
  return '—'
})

const syncExchangeRate = async () => {
  syncingRate.value = true
  try {
    // Fetch rates from CBM API (or scrape)
    await api.post('settings/exchange-rate/fetch/')
    // Refresh rate in store
    await exchangeRate.fetchExchangeRate()
    // Refresh auto-sync status
    await loadExchangeRateStatus()
    rateLastUpdated.value = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
  } catch (err) {
    console.error('Failed to sync exchange rate:', err)
  } finally {
    syncingRate.value = false
  }
}

const loadExchangeRateStatus = async () => {
  try {
    const res = await api.get('settings/exchange-rate/')
    isAutoSync.value = res.data.is_auto_sync !== false
  } catch (err) {
    console.error('Failed to load exchange rate status:', err)
  }
}

const openRateManagement = () => {
  showRateManagementModal.value = true
}

const handleRateSettingsSaved = async () => {
  // Refresh rate and status after settings are saved
  await exchangeRate.fetchExchangeRate()
  await loadExchangeRateStatus()
}

onMounted(async () => {
  await exchangeRate.fetchExchangeRate()
  await loadExchangeRateStatus()
  await featureToggles.fetch()
  try {
    const res = await api.get('settings/exchange-rate/history/', { params: { limit: 1 } })
    if (res.data.rates?.USD) {
      const date = res.data.rates.USD.date
      if (date) {
        const updateDate = new Date(date)
        rateLastUpdated.value = updateDate.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
      }
    }
  } catch (err) {
    console.error('Failed to load rate history:', err)
  }
})

// Menu Items: filter by role then by feature toggles (Service / Installation)
const filteredMenuWithToggles = computed(() => {
  let list = filteredMenu.value
  if (!featureToggles.enable_service) {
    list = list.filter((i) => i.name !== 'Service')
  }
  if (!featureToggles.enable_installation) {
    list = list.filter((i) => i.path !== '/installation/dashboard' && i.path !== '/installation')
  }
  return list
})

const generalItems = computed(() =>
  filteredMenuWithToggles.value.filter((i) =>
    ['Dashboard', 'Sales Request', 'Inventory', 'Sales History', 'Service', 'ကုသမှုမှတ်တမ်း', 'Approve', 'Settings'].includes(
      i.name,
    ),
  ),
)

const managementItems = computed(() =>
  filteredMenuWithToggles.value.filter((i) =>
    ['Products', 'Categories', 'Users Management', 'Shop Location', 'Stock Movement'].includes(
      i.name,
    ),
  ),
)

const accountingItems = computed(() => {
  const role = (authStore.role || localStorage.getItem('user_role') || '').toLowerCase().trim().replace(/\s+/g, '_')
  const canView = ['super_admin', 'owner', 'admin', 'manager'].includes(role)
  if (!canView) return []
  return [
    { name: 'ကုန်ကျစရိတ်', path: '/accounting/expenses', icon: DollarSign },
    { name: 'P&L အစီရင်ခံစာ', path: '/accounting/pl', icon: TrendingUp },
  ]
})

const reportItems = computed(() => {
  const role = (authStore.role || localStorage.getItem('user_role') || '').toLowerCase().trim().replace(/\s+/g, '_')
  const canViewReports = ['super_admin', 'owner', 'manager', 'assistant_manager', 'inventory_manager', 'sale_supervisor', 'sale_staff'].includes(role)
  if (!canViewReports) return []
  return [
    { name: 'အရောင်းအစီရင်ခံစာ', path: '/reports/sales', icon: FileText },
    { name: 'တစ်နေ့တာ ရောင်းအား', path: '/reports/sales-summary', icon: BarChart3 },
    { name: 'ပစ္စည်းစာရင်း', path: '/reports/inventory', icon: BarChart3 },
    { name: 'စက်ပြင်ဝန်ဆောင်မှု', path: '/reports/service', icon: ToolCase },
    { name: 'ဝယ်ယူသူ စာရင်း', path: '/reports/customers', icon: Users },
    { name: 'P&L အစီရင်ခံစာ', path: '/accounting/pl', icon: TrendingUp },
  ]
})

const publicItems = [
  { name: 'စက်ပြင်ခြေရာခံမှု', path: '/repair-track', icon: Wrench },
  { name: 'အာမခံချက်စစ်ဆေးမှု', path: '/warranty-check', icon: Shield },
]

const allMenuItems = [
  {
    name: 'Dashboard',
    path: '/',
    icon: LayoutDashboard,
    roles: [
      'super_admin',
      'owner',
      'admin',
      'manager',
      'assistant_manager',
      'inventory_manager',
      'inventory_staff',
      'sale_staff',
      'sale_supervisor',
    ],
  },
  {
    name: 'Inventory',
    path: '/inventory',
    icon: Box,
    roles: ['super_admin', 'owner', 'admin', 'manager', 'inventory_manager', 'inventory_staff'],
  },

  {
    name: 'Categories',
    path: '/categories',
    icon: Tags,
    roles: ['super_admin', 'owner', 'admin', 'manager', 'inventory_manager'],
  },
  {
    name: 'Products',
    path: '/products',
    icon: Box,
    roles: ['super_admin', 'owner', 'admin', 'manager', 'inventory_manager', 'inventory_staff'],
  },
  {
    name: 'Stock Movement',
    path: '/movements',
    icon: ArrowUpDown,
    roles: ['super_admin', 'owner', 'admin', 'manager', 'inventory_manager', 'inventory_staff'],
  },
  {
    name: 'Shop Location',
    path: '/shop-locations',
    icon: Map,
    roles: ['super_admin', 'owner', 'admin', 'manager'],
  },
  {
    name: 'Users Management',
    path: '/users',
    icon: Users,
    roles: ['super_admin', 'owner', 'admin', 'manager'],
  },
  {
    name: 'Sales Request',
    path: '/sales/pos',
    icon: ShoppingCart,
    roles: ['super_admin', 'owner', 'admin', 'sale_staff', 'sale_supervisor', 'manager', 'assistant_manager'],
  },
  {
    name: 'Sales History',
    path: '/sales/history',
    icon: History,
    roles: [
      'super_admin',
      'owner',
      'admin',
      'manager',
      'assistant_manager',
      'sale_staff',
      'sale_supervisor',
    ],
  },
  {
    name: 'Service',
    path: '/service',
    icon: ToolCase,
    roles: [
      'super_admin',
      'owner',
      'admin',
      'manager',
      'inventory_manager',
      'inventory_staff',
      'sale_supervisor',
      'sale_staff',
    ],
  },
  {
    name: 'ကုသမှုမှတ်တမ်း',
    path: '/treatment-records',
    icon: FileText,
    roles: ['super_admin', 'owner', 'admin', 'manager'],
  },
  {
    name: 'Approve',
    path: '/sales/approve',
    icon: CheckCircle,
    roles: ['super_admin', 'owner', 'admin', 'manager', 'assistant_manager'],
  },
  {
    name: 'Settings',
    path: '/settings',
    icon: Settings,
    roles: ['super_admin', 'owner', 'admin', 'manager'],
  },
  {
    name: 'ကုန်ကျစရိတ်',
    path: '/accounting/expenses',
    icon: DollarSign,
    roles: ['super_admin', 'owner', 'admin', 'manager'],
  },
  {
    name: 'P&L အစီရင်ခံစာ',
    path: '/accounting/pl',
    icon: TrendingUp,
    roles: ['super_admin', 'owner', 'admin', 'manager'],
  },
  {
    name: 'တပ်ဆင်မှု Dashboard',
    path: '/installation/dashboard',
    icon: Wrench,
    roles: ['super_admin', 'owner', 'admin', 'manager'],
  },
  {
    name: 'တပ်ဆင်မှု စီမံခန့်ခွဲမှု',
    path: '/installation',
    icon: ToolCase,
    roles: ['super_admin', 'owner', 'admin', 'manager', 'inventory_manager'],
  },
]

const filteredMenu = computed(() => {
  const rawRole = authStore.role || localStorage.getItem('user_role') || ''
  const userRole = rawRole.toLowerCase().trim().replace(/\s+/g, '_')
  if (!userRole) return []
  return allMenuItems.filter(
    (item) =>
      userRole === 'super_admin' ||
      userRole === 'owner' ||
      userRole === 'admin' ||
      item.roles.includes(userRole),
  )
})

const handleLogout = () => {
  if (confirm('Log out လုပ်မှာ သေချာပါသလား?')) {
    authStore.logout()
    router.push(getLoginPath())
  }
}
</script>

<style scoped>
/* App နဲ့ တူအောင် Inter / system font သုံး (Google Roboto မလိုတော့ timeout မဖြစ်) */
* {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

.glow-effect {
  box-shadow: 0 0 15px rgba(170, 0, 0, 0.15);
  animation: pulse-glow 3s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% {
    box-shadow: 0 0 15px rgba(170, 0, 0, 0.15);
  }
  50% {
    box-shadow: 0 0 25px rgba(170, 0, 0, 0.25);
  }
}

.glow-green {
  box-shadow: 0 0 8px rgba(34, 197, 94, 0.4);
  animation: pulse-glow-green 2s ease-in-out infinite;
}

@keyframes pulse-glow-green {
  0%, 100% {
    box-shadow: 0 0 8px rgba(34, 197, 94, 0.4);
  }
  50% {
    box-shadow: 0 0 15px rgba(34, 197, 94, 0.6);
  }
}

.glow-red {
  box-shadow: 0 0 8px rgba(239, 68, 68, 0.4);
  animation: pulse-glow-red 2s ease-in-out infinite;
}

@keyframes pulse-glow-red {
  0%, 100% {
    box-shadow: 0 0 8px rgba(239, 68, 68, 0.4);
  }
  50% {
    box-shadow: 0 0 15px rgba(239, 68, 68, 0.6);
  }
}

.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
</style>
