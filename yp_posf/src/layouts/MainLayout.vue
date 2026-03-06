<template>
  <!-- Standard natural scrolling layout: page scrolls with browser; sticky header; sidebar in-flow on desktop. -->
  <div class="flex w-full bg-background text-premium font-sans app-shell">
    <aside
      class="sidebar-column flex-none transition-[width] duration-[400ms] ease-[cubic-bezier(0.4,0,0.2,1)]"
      :style="{ '--sidebar-current-width': effectiveSidebarWidth }"
    >
      <Sidebar
        v-model:mobileOpen="mobileSidebarOpen"
        v-model:collapsed="sidebarCollapsed"
        :collapsed="sidebarCollapsed"
        @hover-start="sidebarHover = true"
        @hover-end="sidebarHover = false"
      />
    </aside>
    <div class="flex flex-1 flex-col min-w-0">
      <header class="sticky top-0 z-50 flex-none shrink-0 min-h-[56px]">
        <Topbar @toggle-sidebar="mobileSidebarOpen = !mobileSidebarOpen" />
        <LicenseBanner />
      </header>
      <main class="flex-1 min-w-0 main-content-safe bg-[var(--color-bg-light)] flex flex-col min-h-0">
        <div class="page-content flex-1 flex flex-col min-h-0 w-full max-w-full">
          <RouterView />
        </div>
      </main>
      <div class="md:hidden h-[72px] shrink-0 flex-none" aria-hidden="true"></div>
    </div>

    <!-- Mobile: bottom nav — 48px touch targets, safe-area, white/black theme -->
    <nav
      class="md:hidden fixed bottom-0 left-0 right-0 z-40 flex items-center justify-around bg-[var(--color-bg-card)] border-t border-[var(--color-border)] shadow-[0_-4px_20px_rgba(0,0,0,0.06)] transition-all duration-300 ease-out"
      style="padding-left: env(safe-area-inset-left); padding-right: env(safe-area-inset-right); padding-top: 10px; padding-bottom: max(10px, env(safe-area-inset-bottom)); min-height: 64px;"
    >
      <RouterLink
        v-for="nav in mobileBottomNav"
        :key="nav.path"
        :to="nav.path"
        class="min-w-[48px] min-h-[48px] flex items-center justify-center rounded-xl text-[var(--color-text-muted)] hover:text-[var(--color-primary)] hover:bg-[var(--color-bg-light)] transition-all duration-200 touch-manipulation active:scale-95"
        :class="{ '!text-[var(--color-primary)] !bg-[var(--color-bg-light)] font-semibold': $route.path === nav.path || ($route.path.startsWith(nav.path + '/') && nav.path !== '/') }"
      >
        <component :is="nav.icon" class="w-6 h-6 shrink-0" :stroke-width="1.8" />
      </RouterLink>
    </nav>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { RouterLink } from 'vue-router'
import { ShoppingCart, Package, BarChart3, Settings } from 'lucide-vue-next'
import Sidebar from '@/components/SidebarLoyverse.vue'
import Topbar from '@/components/Topbar.vue'
import LicenseBanner from '@/components/LicenseBanner.vue'

const route = useRoute()
const mobileSidebarOpen = ref(false)
// POS style: sidebar expanded by default so labels are always visible (not dashboard icon-only rail)
const sidebarCollapsed = ref(false)
const sidebarHover = ref(false)

// When collapsed + hover, expand sidebar (main content shrinks); when expanded or not collapsed, use expanded width
const effectiveSidebarWidth = computed(() => {
  const mini = 'var(--sidebar-mini-width)'
  const expanded = 'var(--sidebar-expanded-width)'
  if (sidebarCollapsed.value && !sidebarHover.value) return mini
  return expanded
})

const mobileBottomNav = [
  { icon: ShoppingCart, path: '/sales/pos' },
  { icon: Package, path: '/products' },
  { icon: BarChart3, path: '/reports/sales-summary' },
  { icon: Settings, path: '/settings' },
]

watch(() => route.path, () => {
  mobileSidebarOpen.value = false
})
</script>

<style scoped>
.app-shell {
  width: 100%;
}
.sidebar-column {
  width: var(--sidebar-current-width);
}
@media (max-width: 1023px) {
  .sidebar-column {
    width: 0 !important;
    min-width: 0 !important;
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 60;
  }
}
@media (min-width: 1024px) {
  .sidebar-column {
    width: var(--sidebar-current-width);
  }
}
.main-content-safe {
  padding-left: env(safe-area-inset-left);
  padding-right: env(safe-area-inset-right);
}
</style>
