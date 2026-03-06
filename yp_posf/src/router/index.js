import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'

const routes = [
  // Public routes (no auth)
  {
    path: '/repair-track',
    name: 'RepairTrack',
    component: () => import('@/views/public/RepairTrack.vue'),
    meta: { public: true },
  },
  {
    path: '/warranty-check',
    name: 'WarrantyCheck',
    component: () => import('@/views/public/WarrantyCheck.vue'),
    meta: { public: true },
  },
  // /app/pos ရောက်ရင် POS ပြအောင် redirect (base /app/ သုံးတဲ့အခါ)
  { path: '/pos', redirect: '/sales/pos' },
  {
    path: '/',
    component: MainLayout,
    children: [
      {
        path: '',
        name: 'Home',
        redirect: '/sales/pos',
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { layout: 'MainLayout' },
      },
      {
        path: 'inventory',
        name: 'Inventory',
        component: () => import('@/views/Inventory.vue'),
      },
      {
        path: '/categories',
        name: 'Categories',
        component: () => import('@/views/inventory/CategoryManagement.vue'),
        meta: { layout: 'MainLayout' },
      },
      {
        path: '/products',
        name: 'Products',
        component: () => import('@/views/items/ItemListPage.vue'),
        meta: { layout: 'MainLayout' },
      },
      {
        path: '/products/import',
        name: 'ProductImport',
        component: () => import('@/views/inventory/ProductImport.vue'),
        meta: { layout: 'MainLayout' },
      },
      {
        path: '/items',
        name: 'ItemList',
        component: () => import('@/views/items/ItemListPage.vue'),
        meta: { layout: 'MainLayout' },
      },
      {
        path: '/movements',
        name: 'Stock Movement',
        component: () => import('@/views/inventory/InventoryMovement.vue'),
        meta: { layout: 'MainLayout' },
      },
      {
        path: '/shop-locations',
        name: 'Shop Locations',
        component: () => import('@/views/inventory/LocationManagement.vue'),
        meta: { layout: 'MainLayout' },
      },
      {
        path: '/inventory/sets',
        name: 'BundleSets',
        component: () => import('@/views/inventory/BundleSetManagement.vue'),
        meta: { layout: 'MainLayout' },
      },
      {
        path: '/inventory/transfer',
        name: 'InventoryTransfer',
        component: () => import('@/views/inventory/TransferUI.vue'),
        meta: { requiresAuth: true, role: 'manager' }, // Manager အဆင့်ပဲ ဝင်လို့ရအောင် သတ်မှတ်ခြင်း
      },
      // {
      //   path: 'sales',
      //   name: 'Sales',
      //   component: () => import('@/views/Sales.vue'),
      // },
      {
        path: 'sales/history',
        name: 'SalesHistory',
        component: () => import('@/views/sales/SaleHistory.vue'),
      },
      {
        path: '/sales/pos',
        name: 'SalesRequest',
        component: () => import('@/views/sales/SalesRequest.vue'),
      },
      {
        path: '/sales/approve',
        name: 'Approve',
        component: () => import('@/views/sales/AdminApproval.vue'),
      },
      {
        path: '/service',
        name: 'Service',
        component: () => import('@/views/services/ServiceManagement.vue'),
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/UserManagement.vue'),
      },
      {
        path: 'users/roles',
        name: 'Roles',
        component: () => import('@/views/RoleManagement.vue'),
      },
      {
        path: 'reports/sales',
        name: 'SalesReport',
        component: () => import('@/views/reports/SalesReport.vue'),
      },
      {
        path: 'reports/sales-summary',
        name: 'SalesSummaryReport',
        component: () => import('@/views/reports/SalesSummaryReport.vue'),
      },
      {
        path: 'reports/sale-by-item',
        name: 'SaleByItemReport',
        component: () => import('@/views/reports/SaleByItemReport.vue'),
      },
      {
        path: 'reports/sales-by-category',
        name: 'SalesByCategoryReport',
        component: () => import('@/views/reports/SalesByCategoryReport.vue'),
      },
      {
        path: 'reports/sales-by-employee',
        name: 'SalesByEmployeeReport',
        component: () => import('@/views/reports/SalesByEmployeeReport.vue'),
      },
      {
        path: 'reports/sales-by-payment',
        name: 'SalesByPaymentReport',
        component: () => import('@/views/reports/SalesByPaymentReport.vue'),
      },
      {
        path: 'reports/receipts',
        name: 'ReceiptsReport',
        component: () => import('@/views/reports/ReceiptsReport.vue'),
      },
      {
        path: 'reports/sales-by-modifier',
        name: 'SalesByModifierReport',
        component: () => import('@/views/reports/SalesByModifierReport.vue'),
      },
      {
        path: 'reports/discount',
        name: 'DiscountReport',
        component: () => import('@/views/reports/DiscountReport.vue'),
      },
      {
        path: 'reports/taxes',
        name: 'TaxesReport',
        component: () => import('@/views/reports/TaxesReport.vue'),
      },
      {
        path: 'reports/shift',
        name: 'ShiftReport',
        component: () => import('@/views/reports/ShiftReport.vue'),
      },
      {
        path: 'reports/inventory',
        name: 'InventoryReport',
        component: () => import('@/views/reports/InventoryReport.vue'),
      },
      {
        path: 'reports/service',
        name: 'ServiceReport',
        component: () => import('@/views/reports/ServiceReport.vue'),
      },
      {
        path: 'reports/customers',
        name: 'CustomerReport',
        component: () => import('@/views/reports/CustomerReport.vue'),
      },
      {
        path: 'items/list',
        name: 'ItemList',
        component: () => import('@/views/items/ItemListPage.vue'),
      },
      {
        path: 'items/categories',
        name: 'ItemsCategories',
        component: () => import('@/views/inventory/CategoryManagement.vue'),
      },
      {
        path: 'items/modifiers',
        name: 'ItemsModifiers',
        component: () => import('@/views/items/ItemsModifiers.vue'),
      },
      {
        path: 'items/discounts',
        name: 'ItemsDiscounts',
        component: () => import('@/views/items/ItemsDiscounts.vue'),
      },
      {
        path: 'inventory/purchase-orders',
        name: 'PurchaseOrders',
        component: () => import('@/views/inventory/PurchaseOrdersPage.vue'),
      },
      {
        path: 'inventory/transfer-orders',
        name: 'TransferOrders',
        component: () => import('@/views/inventory/TransferUI.vue'),
      },
      {
        path: 'inventory/stock-counts',
        name: 'StockCounts',
        component: () => import('@/views/inventory/StockCountsPage.vue'),
      },
      {
        path: 'inventory/history',
        name: 'InventoryHistory',
        component: () => import('@/views/inventory/InventoryMovement.vue'),
      },
      {
        path: '/accounting/expenses',
        name: 'ExpenseManagement',
        component: () => import('@/views/accounting/ExpenseManagement.vue'),
      },
      {
        path: '/accounting/pl',
        name: 'ProfitLossReport',
        component: () => import('@/views/accounting/ProfitLossReport.vue'),
      },
      {
        path: '/installation',
        name: 'InstallationManagement',
        component: () => import('@/views/installation/InstallationManagement.vue'),
      },
      {
        path: '/installation/dashboard',
        name: 'InstallationDashboard',
        component: () => import('@/views/installation/InstallationDashboard.vue'),
      },
      {
        path: '/installation/:id',
        name: 'InstallationDetail',
        component: () => import('@/views/installation/InstallationDetail.vue'),
      },
      {
        path: '/treatment-records',
        name: 'TreatmentRecords',
        component: () => import('@/views/services/TreatmentRecords.vue'),
        meta: { layout: 'MainLayout' },
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue'),
      },
      {
        path: 'settings/shifts',
        name: 'ShiftManagement',
        component: () => import('@/views/settings/ShiftManagement.vue'),
      },
    ],
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/Login.vue'),
    meta: { public: true },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/Register.vue'),
    meta: { public: true },
  },
  {
    path: '/setup-wizard',
    name: 'SetupWizard',
    component: () => import('@/views/SetupWizard.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/license-activate',
    name: 'LicenseActivation',
    component: () => import('@/views/LicenseActivation.vue'),
    meta: { public: true },
  },
  {
    path: '/trial-expired',
    name: 'TrialExpired',
    component: () => import('@/views/TrialExpired.vue'),
    meta: { public: true },
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: () => import('@/views/ForgotPassword.vue'),
    meta: { public: true },
  },
  {
    path: '/reset-password',
    name: 'ResetPassword',
    component: () => import('@/views/ResetPassword.vue'),
    meta: { public: true },
  },
  // Catch-all: unknown paths show 404 page (no blank screen)
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { public: true },
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

/** Base path for redirects so we get localhost:port/app/... not localhost:port/... (avoids nginx 404 when SPA is under /app/) */
export function getAppPath(subpath) {
  const base = (import.meta.env.BASE_URL || '/').replace(/\/+$/, '')
  const path = subpath.startsWith('/') ? subpath.slice(1) : subpath
  return base ? `${base}/${path}` : `/${path}`
}
export function getLoginPath() {
  return getAppPath('/login')
}

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')
  const isPublic = to.meta?.public === true

  if (isPublic) {
    if (['login', 'register', 'ForgotPassword', 'ResetPassword'].includes(to.name)) {
      if (token && to.name !== 'ForgotPassword' && to.name !== 'ResetPassword') next({ name: 'SetupWizard' })
      else next()
    } else {
      next()
    }
    return
  }
  if (to.name !== 'login' && !token) {
    next({ name: 'login' })
  } else if (to.name === 'login' && token) {
    next({ name: 'SetupWizard' })
  } else {
    next()
  }
})

// ဒီ line ပါမှ main.js က ယူသုံးလို့ရမှာပါ
export default router
