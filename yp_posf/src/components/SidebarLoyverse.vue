<template>
  <!-- Minimalist POS Sidebar: white, 4 groups (POS, Items, Inventory, Reports) + Settings bottom. Icon-only when collapsed. -->
  <div
    v-show="mobileOpen"
    class="fixed inset-0 bg-black/40 z-[55] lg:hidden"
    aria-hidden="true"
    @click="$emit('update:mobileOpen', false)"
  />
  <aside
    class="sidebar-rail fixed inset-y-0 left-0 z-[60] flex flex-col min-h-screen lg:min-h-0 w-full max-w-[85vw] lg:max-w-none border-r border-gray-200 lg:relative lg:z-auto lg:translate-x-0 transition-all duration-300 ease-out bg-white"
    style="--sidebar-fixed-width: 280px;"
    :class="mobileOpen ? 'translate-x-0' : '-translate-x-full'"
    @mouseenter="onSidebarMouseEnter"
    @mouseleave="onSidebarMouseLeave"
  >
    <!-- Logo row: compact, icon-only when collapsed -->
    <div class="flex items-center gap-2 p-3 flex-shrink-0 border-b border-[var(--color-border)] min-h-[52px]">
      <div class="w-8 h-8 rounded-lg bg-[var(--color-bg-card)] border border-[var(--color-border)] flex items-center justify-center shrink-0 overflow-hidden">
        <img v-if="shopLogo && !logoError" :src="shopLogo" alt="Logo" class="w-8 h-8 object-contain" @error="logoError = true" />
        <span v-else class="text-xs font-semibold text-[var(--color-primary)]">{{ (shopName || 'POS').slice(0, 2) }}</span>
      </div>
      <span v-show="showLabels" class="text-sm font-semibold text-[var(--color-fg)] truncate">{{ shopName || 'POS' }}</span>
      <button
        type="button"
        class="hidden lg:flex ml-auto p-1.5 rounded text-[var(--color-fg-muted)] hover:bg-[var(--color-bg-light)] hover:text-[var(--color-primary)] transition-colors shrink-0"
        :aria-label="showLabels ? 'Collapse' : 'Expand'"
        @click="$emit('update:collapsed', !collapsed)"
      >
        <ChevronLeft v-if="showLabels" class="w-4 h-4" />
        <ChevronRight v-else class="w-4 h-4" />
      </button>
      <button
        type="button"
        class="lg:hidden p-1.5 rounded text-[var(--color-fg-muted)] hover:bg-[var(--color-bg-card)] ml-auto"
        aria-label="Close"
        @click="$emit('update:mobileOpen', false)"
      >
        <X class="w-4 h-4" />
      </button>
    </div>

    <!-- Nav: role-based (Cashier: POS + Reports only; Inventory: Inventory only; Manager/Owner: full) -->
    <nav class="flex-1 overflow-y-auto py-2 min-h-0">
      <!-- 1. POS (hidden for inventory-only role) -->
      <div v-if="showPos" class="mb-1">
        <RouterLink to="/sales/pos" class="sidebar-nav-item" :class="{ 'sidebar-nav-item-active': $route.path === '/sales/pos' }">
          <ShoppingCart class="w-4 h-4 shrink-0" stroke-width="2" />
          <span v-show="showLabels">POS</span>
        </RouterLink>
      </div>

      <!-- 2. Dashboard -->
      <div v-if="showDashboard" class="mb-1">
        <RouterLink to="/dashboard" class="sidebar-nav-item" :class="{ 'sidebar-nav-item-active': $route.path === '/dashboard' }">
          <LayoutDashboard class="w-4 h-4 shrink-0" stroke-width="2" />
          <span v-show="showLabels">{{ t('dashboard') }}</span>
        </RouterLink>
      </div>

      <!-- 3. Items (Owner, Manager only; hidden for Cashier, Inventory) -->
      <div v-if="showItems" class="mb-1">
        <button
          type="button"
          class="sidebar-nav-item w-full justify-between"
          :class="{ 'sidebar-nav-item-active': isItemsSection }"
          @click="itemsOpen = !itemsOpen"
        >
          <span class="flex items-center gap-3">
            <Package class="w-4 h-4 shrink-0" stroke-width="2" />
            <span v-show="showLabels">Items</span>
          </span>
          <ChevronDown v-show="showLabels" class="w-4 h-4 shrink-0 transition-transform" :class="itemsOpen ? 'rotate-180' : ''" />
        </button>
        <div v-show="itemsOpen && showLabels" class="ml-3 pl-2 border-l border-gray-200 space-y-0.5 mt-0.5 mb-1">
          <RouterLink to="/items/list" class="sidebar-nav-subitem" active-class="sidebar-nav-item-active">Item List</RouterLink>
          <RouterLink to="/products/import" class="sidebar-nav-subitem" active-class="sidebar-nav-item-active">Import (Excel/CSV)</RouterLink>
          <RouterLink to="/items/categories" class="sidebar-nav-subitem" active-class="sidebar-nav-item-active">Categories</RouterLink>
          <RouterLink to="/items/modifiers" class="sidebar-nav-subitem" active-class="sidebar-nav-item-active">Modifiers</RouterLink>
          <RouterLink to="/items/discounts" class="sidebar-nav-subitem" active-class="sidebar-nav-item-active">Discounts</RouterLink>
        </div>
      </div>

      <!-- 4. Inventory (Owner, Manager, Inventory role) -->
      <div v-if="showInventory" class="mb-1">
        <button
          type="button"
          class="sidebar-nav-item w-full justify-between"
          :class="{ 'sidebar-nav-item-active': isInventorySection }"
          @click="inventoryOpen = !inventoryOpen"
        >
          <span class="flex items-center gap-3">
            <Warehouse class="w-4 h-4 shrink-0" stroke-width="2" />
            <span v-show="showLabels">{{ t('inventory') }}</span>
          </span>
          <ChevronDown v-show="showLabels" class="w-4 h-4 shrink-0 transition-transform" :class="inventoryOpen ? 'rotate-180' : ''" />
        </button>
        <div v-show="inventoryOpen && showLabels" class="ml-3 pl-2 border-l border-gray-200 space-y-0.5 mt-0.5 mb-1">
          <RouterLink to="/shop-locations" class="sidebar-nav-subitem" active-class="sidebar-nav-item-active">Locations / ဆိုင်ခွဲ</RouterLink>
          <RouterLink to="/inventory/sets" class="sidebar-nav-subitem" active-class="sidebar-nav-item-active">အတွဲ (Set)</RouterLink>
          <RouterLink to="/inventory/purchase-orders" class="sidebar-nav-subitem" active-class="sidebar-nav-item-active">Purchase Orders</RouterLink>
          <RouterLink to="/inventory/transfer-orders" class="sidebar-nav-subitem" active-class="sidebar-nav-item-active">Transfer Orders</RouterLink>
          <RouterLink to="/movements" class="sidebar-nav-subitem" active-class="sidebar-nav-item-active">Inbound / Outbound</RouterLink>
          <RouterLink to="/inventory/stock-counts" class="sidebar-nav-subitem" active-class="sidebar-nav-item-active">Stock Counts</RouterLink>
        </div>
      </div>

      <!-- 5. Reports (Sales Summary, Receipts, Shift) -->
      <div v-if="showReportsSection" class="mb-1">
        <button
          type="button"
          class="sidebar-nav-item w-full justify-between"
          :class="{ 'sidebar-nav-item-active': isReportsSection }"
          @click="reportsOpen = !reportsOpen"
        >
          <span class="flex items-center gap-3">
            <BarChart2 class="w-4 h-4 shrink-0" stroke-width="2" />
            <span v-show="showLabels">{{ t('reports') }}</span>
          </span>
          <ChevronDown v-show="showLabels" class="w-4 h-4 shrink-0 transition-transform" :class="reportsOpen ? 'rotate-180' : ''" />
        </button>
        <div v-show="reportsOpen && showLabels" class="ml-3 pl-2 border-l border-gray-200 space-y-0.5 mt-0.5 mb-1">
          <RouterLink to="/sales/history" class="sidebar-nav-subitem" active-class="sidebar-nav-item-active">{{ t('sales_history') }}</RouterLink>
          <RouterLink to="/reports/sales-summary" class="sidebar-nav-subitem" active-class="sidebar-nav-item-active">Sales Summary</RouterLink>
          <RouterLink to="/reports/receipts" class="sidebar-nav-subitem" active-class="sidebar-nav-item-active">Receipts</RouterLink>
          <RouterLink to="/reports/shift" class="sidebar-nav-subitem" active-class="sidebar-nav-item-active">Shift Report</RouterLink>
          <RouterLink v-if="showAccounting" to="/settings/shifts" class="sidebar-nav-subitem" active-class="sidebar-nav-item-active">Shift (CRUD)</RouterLink>
        </div>
      </div>

      <!-- 6. Accounting (Owner, Manager only) -->
      <div v-if="showAccounting" class="mb-1">
        <button
          type="button"
          class="sidebar-nav-item w-full justify-between"
          :class="{ 'sidebar-nav-item-active': isAccountingSection }"
          @click="accountingOpen = !accountingOpen"
        >
          <span class="flex items-center gap-3">
            <TrendingUp class="w-4 h-4 shrink-0" stroke-width="2" />
            <span v-show="showLabels">{{ t('accounting') }}</span>
          </span>
          <ChevronDown v-show="showLabels" class="w-4 h-4 shrink-0 transition-transform" :class="accountingOpen ? 'rotate-180' : ''" />
        </button>
        <div v-show="accountingOpen && showLabels" class="ml-3 pl-2 border-l border-gray-200 space-y-0.5 mt-0.5 mb-1">
          <RouterLink to="/accounting/pl" class="sidebar-nav-subitem" active-class="sidebar-nav-item-active">{{ t('pl_report') }}</RouterLink>
          <RouterLink to="/accounting/expenses" class="sidebar-nav-subitem" active-class="sidebar-nav-item-active">{{ t('expenses') }}</RouterLink>
        </div>
      </div>

      <!-- 7. Service (repair) - toggle -->
      <div v-if="featureToggles.enable_service" class="mb-1">
        <RouterLink to="/service" class="sidebar-nav-item" :class="{ 'sidebar-nav-item-active': $route.path === '/service' }">
          <ToolCase class="w-4 h-4 shrink-0" stroke-width="2" />
          <span v-show="showLabels">{{ t('service') }}</span>
        </RouterLink>
      </div>

      <!-- 8. Treatment Records (ဖွင့်/ပိတ် သီးခြား) -->
      <div v-if="featureToggles.enable_treatment_records" class="mb-1">
        <RouterLink to="/treatment-records" class="sidebar-nav-item" :class="{ 'sidebar-nav-item-active': $route.path === '/treatment-records' }">
          <FileText class="w-4 h-4 shrink-0" stroke-width="2" />
          <span v-show="showLabels">{{ t('treatment_records') }}</span>
        </RouterLink>
      </div>

      <!-- 9. Installation (solar / service) - toggle -->
      <div v-if="featureToggles.enable_installation" class="mb-1">
        <RouterLink to="/installation" class="sidebar-nav-item" :class="{ 'sidebar-nav-item-active': $route.path.startsWith('/installation') }">
          <Wrench class="w-4 h-4 shrink-0" stroke-width="2" />
          <span v-show="showLabels">{{ t('installation') }}</span>
        </RouterLink>
      </div>
    </nav>

    <!-- Settings + Logout at bottom -->
    <div class="p-2 border-t border-[var(--color-border)] flex-shrink-0 bg-white space-y-0.5">
      <RouterLink to="/settings" class="sidebar-nav-item" :class="{ 'sidebar-nav-item-active': $route.path === '/settings' }">
        <Settings class="w-4 h-4 shrink-0" stroke-width="2" />
        <span v-show="showLabels">{{ t('settings') }}</span>
      </RouterLink>
      <button
        type="button"
        class="sidebar-nav-item w-full text-left justify-start text-red-600 hover:bg-red-50 hover:text-red-700"
        :class="showLabels ? 'justify-start' : 'justify-center'"
        @click="handleLogout"
      >
        <LogOut class="w-4 h-4 shrink-0" stroke-width="2" />
        <span v-show="showLabels">{{ t('logout') }}</span>
      </button>
    </div>
  </aside>
</template>

<script setup>
import { computed, ref, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { getLoginPath } from '@/router'
import { useShopSettingsStore } from '@/stores/shopSettings'
import { useAuthStore } from '@/stores/auth'
import {
  BarChart2,
  Package,
  Warehouse,
  ShoppingCart,
  Settings,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  LogOut,
  X,
  LayoutDashboard,
  TrendingUp,
  Wrench,
  ToolCase,
  FileText,
} from 'lucide-vue-next'
import { useFeatureTogglesStore } from '@/stores/featureToggles'
import { useI18n } from '@/composables/useI18n'

const { t } = useI18n()
const props = defineProps({
  mobileOpen: { type: Boolean, default: false },
  collapsed: { type: Boolean, default: true },
})
const emit = defineEmits(['update:mobileOpen', 'update:collapsed', 'hover-start', 'hover-end'])

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const sidebarHover = ref(false)
const showLabels = computed(() => !props.collapsed || sidebarHover.value)

const role = computed(() => (authStore.role || '').toLowerCase())
const isOwner = computed(() => ['owner', 'admin', 'super', 'superuser', 'super_admin'].includes(role.value))
const isCashier = computed(() => role.value === 'cashier')
const isManager = computed(() => role.value === 'manager')
const isInventoryRole = computed(() => ['inventory', 'stock'].includes(role.value))

const showPos = computed(() => !isInventoryRole.value)
const showDashboard = computed(() => !isInventoryRole.value)
const showItems = computed(() => isOwner.value || isManager.value)
const showInventory = computed(() => isOwner.value || isManager.value || isInventoryRole.value)
const showReportsSection = computed(() => !isInventoryRole.value)
const showAccounting = computed(() => isOwner.value || isManager.value)

const isItemsSection = computed(() => {
  const p = route.path
  return p.startsWith('/items') || p === '/products' || p.startsWith('/products/') || p === '/categories'
})
const isInventorySection = computed(() => {
  const p = route.path
  return p.startsWith('/inventory') || p === '/shop-locations' || p === '/movements'
})
const isReportsSection = computed(() => {
  const p = route.path
  return p.startsWith('/reports') || p === '/sales/history' || p === '/settings/shifts'
})
const isAccountingSection = computed(() => route.path.startsWith('/accounting'))

const reportsOpen = ref(isReportsSection.value)
const itemsOpen = ref(isItemsSection.value)
const inventoryOpen = ref(isInventorySection.value)
const accountingOpen = ref(isAccountingSection.value)

watch(() => route.path, (path) => {
  reportsOpen.value = path.startsWith('/reports') || path === '/sales/history' || path === '/settings/shifts'
  itemsOpen.value = path.startsWith('/items') || path === '/products' || path.startsWith('/products/') || path === '/categories'
  inventoryOpen.value = path.startsWith('/inventory') || path === '/shop-locations' || path === '/movements'
  accountingOpen.value = path.startsWith('/accounting')
})

function onSidebarMouseEnter() {
  sidebarHover.value = true
  emit('hover-start')
}
function onSidebarMouseLeave() {
  sidebarHover.value = false
  emit('hover-end')
}

const logoError = ref(false)
const shopStore = useShopSettingsStore()
const shopLogo = computed(() => shopStore.logo_url)
const shopName = computed(() => shopStore.displayName)
const featureToggles = useFeatureTogglesStore()

onMounted(() => {
  featureToggles.fetch()
})

function handleLogout() {
  if (confirm('Log out?')) {
    authStore.logout()
    router.push(getLoginPath())
  }
}
</script>

<style scoped>
.sidebar-rail {
  background: #ffffff;
}
/* POS style: comfortable tap targets and readable labels */
.sidebar-nav-item {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 0.75rem;
  padding: 0.65rem 0.85rem;
  margin: 0 0.35rem;
  border-radius: 10px;
  font-size: 1rem;
  font-weight: 500;
  color: #1a1a1a;
  transition: background 0.15s, color 0.15s;
  text-decoration: none;
  border: none;
  background: transparent;
  width: calc(100% - 0.7rem);
  cursor: pointer;
  text-align: left;
  writing-mode: horizontal-tb;
  white-space: nowrap;
}
.sidebar-nav-item:hover {
  background: var(--color-bg-light);
  color: var(--color-primary);
}
.sidebar-nav-item-active {
  background: var(--color-bg-light);
  color: var(--color-primary);
  font-weight: 600;
}
.sidebar-nav-subitem {
  display: block;
  padding: 0.5rem 0.85rem;
  font-size: 0.95rem;
  color: var(--color-text);
  border-radius: 8px;
  transition: background 0.15s, color 0.15s;
  text-decoration: none;
  writing-mode: horizontal-tb;
}
.sidebar-nav-subitem:hover {
  background: var(--color-bg-light);
  color: var(--color-primary);
}
</style>
