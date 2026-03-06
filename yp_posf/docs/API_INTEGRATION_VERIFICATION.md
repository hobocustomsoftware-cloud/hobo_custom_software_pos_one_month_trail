# API Integration Verification: Frontend ↔ Backend

Frontend uses `api` (axios) with `baseURL: '/api/'`. All paths below are relative to that (e.g. `staff/items/` → `GET /api/staff/items/`).

## 1. Auth & License

| Frontend Call | Full URL | Backend Route | Status |
|---------------|----------|---------------|--------|
| `api.post('token/', { username, password })` | POST /api/token/ | WeldingProject/urls.py → TokenObtainPairView | ✅ |
| `api.get('core/me/')` | GET /api/core/me/ | core/urls.py → UserDetailView | ✅ |
| `api.get('license/status/')` | GET /api/license/status/ | license/urls.py → LicenseStatusView | ✅ |
| `api.post('license/activate/', { license_key })` | POST /api/license/activate/ | license/urls.py → LicenseActivateView | ✅ |
| `api.post('core/register/', payload)` | POST /api/core/register/ | core/urls.py → RegisterView | ✅ |
| `api.post('core/forgot-password/', { username })` | POST /api/core/forgot-password/ | core/urls.py → ForgotPasswordView | ✅ |
| `api.post('core/reset-password/', ...)` | POST /api/core/reset-password/ | core/urls.py → ResetPasswordView | ✅ |

## 2. Shop & Settings

| Frontend Call | Full URL | Backend Route | Status |
|---------------|----------|---------------|--------|
| `api.get('core/shop-settings/')` | GET /api/core/shop-settings/ | WeldingProject/urls.py → ShopSettingsView | ✅ |
| `api.put('core/shop-settings/', formData)` | PUT /api/core/shop-settings/ | WeldingProject/urls.py → ShopSettingsView | ✅ |
| `api.get('settings/business-type/')` | GET /api/settings/business-type/ | inventory/urls.py → BusinessTypeSettingView | ✅ |
| `api.patch('settings/business-type/', { business_type })` | PATCH /api/settings/business-type/ | inventory/urls.py → BusinessTypeSettingView | ✅ |
| `api.get('settings/exchange-rate/')` | GET /api/settings/exchange-rate/ | inventory/urls.py → GlobalSettingExchangeRateView | ✅ |
| `api.patch('settings/exchange-rate/', ...)` | PATCH /api/settings/exchange-rate/ | inventory/urls.py → GlobalSettingExchangeRateView | ✅ |
| `api.post('settings/exchange-rate/fetch/')` | POST /api/settings/exchange-rate/fetch/ | inventory/urls.py → ExchangeRateFetchView | ✅ |
| `api.get('settings/exchange-rate/history/', { params })` | GET /api/settings/exchange-rate/history/ | inventory/urls.py → ExchangeRateHistoryView | ✅ |
| `api.get('settings/exchange-rate/adjustments/')` | GET /api/settings/exchange-rate/adjustments/ | inventory/urls.py → ExchangeRateAdjustmentsView | ✅ |
| `api.post('settings/exchange-rate/adjustments/', ...)` | POST /api/settings/exchange-rate/adjustments/ | inventory/urls.py → (adjustments) | ✅ |

## 3. POS & Sales

| Frontend Call | Full URL | Backend Route | Status |
|---------------|----------|---------------|--------|
| `api.get('staff/items/')` | GET /api/staff/items/ | inventory/urls.py → ProductListAPIView | ✅ |
| `api.post('sales/request/', payload)` | POST /api/sales/request/ | inventory/urls.py → SaleRequestCreateView | ✅ |
| `api.get('payment-methods/list/')` or `api.get('payment-methods/')` | GET /api/payment-methods/list/ or /api/payment-methods/ | inventory/urls.py → PaymentMethodListAPIView or ViewSet list | ✅ |
| `api.get('payment-methods/')` | GET /api/payment-methods/ | inventory/urls.py → PaymentMethodViewSet | ✅ |
| `api.put('payment-methods/<id>/', formData)` | PUT /api/payment-methods/:id/ | inventory/urls.py → PaymentMethodViewSet | ✅ |
| `api.post('payment-methods/', formData)` | POST /api/payment-methods/ | inventory/urls.py → PaymentMethodViewSet | ✅ |
| `api.patch('payment-methods/<id>/', { is_active })` | PATCH /api/payment-methods/:id/ | inventory/urls.py → PaymentMethodViewSet | ✅ |
| `api.delete('payment-methods/<id>/')` | DELETE /api/payment-methods/:id/ | inventory/urls.py → PaymentMethodViewSet | ✅ |
| `api.get('invoice/<id>/')` | GET /api/invoice/:id/ | inventory/urls.py → InvoiceDetailView | ✅ |
| `api.get('invoice/<id>/pdf/', { responseType: 'blob' })` | GET /api/invoice/:id/pdf/ | inventory/urls.py → InvoicePDFView | ✅ |
| `api.post('sales/<id>/upload-payment-proof/', formData)` | POST /api/sales/:id/upload-payment-proof/ | inventory/urls.py → PaymentProofUploadView | ✅ |

## 4. Products, Categories, Search

| Frontend Call | Full URL | Backend Route | Status |
|---------------|----------|---------------|--------|
| `api.get('products/search/', { params: { q } })` | GET /api/products/search/?q= | inventory/urls.py → ProductSearchView | ✅ |
| `api.get('categories/')` | GET /api/categories/ | inventory/urls.py → CategoryViewSet list | ✅ |
| `api.get('products-admin/', { params })` | GET /api/products-admin/ | inventory/urls.py → ProductViewSet list | ✅ |
| `api.post('products-admin/', productData)` | POST /api/products-admin/ | inventory/urls.py → ProductViewSet create | ✅ |
| `api.patch('products-admin/<id>/', productData)` | PATCH /api/products-admin/:id/ | inventory/urls.py → ProductViewSet partial_update | ✅ |
| `api.delete('products-admin/<id>/')` | DELETE /api/products-admin/:id/ | inventory/urls.py → ProductViewSet destroy | ✅ |
| `api.post('products-admin/<id>/clone/')` | POST /api/products-admin/:id/clone/ | inventory/urls.py → ProductCloneView | ✅ |
| `api.get('product-specifications/', { params: { product_id } })` | GET /api/product-specifications/?product_id= | inventory/urls.py → ProductSpecificationViewSet | ✅ |
| `api.post('product-specifications/', ...)` | POST /api/product-specifications/ | inventory/urls.py → ProductSpecificationViewSet | ✅ |
| `api.delete('product-specifications/<id>/')` | DELETE /api/product-specifications/:id/ | inventory/urls.py → ProductSpecificationViewSet | ✅ |
| `api.patch('categories/<id>/', form)` | PATCH /api/categories/:id/ | inventory/urls.py → CategoryViewSet | ✅ |
| `api.post('categories/', form)` | POST /api/categories/ | inventory/urls.py → CategoryViewSet | ✅ |
| `api.delete('categories/<id>/')` | DELETE /api/categories/:id/ | inventory/urls.py → CategoryViewSet | ✅ |

## 5. Customers

| Frontend Call | Full URL | Backend Route | Status |
|---------------|----------|---------------|--------|
| `api.get('customers/')` | GET /api/customers/ | customer/urls.py → CustomerListCreateView (list) | ✅ |
| `api.post('customers/', newCustomer)` | POST /api/customers/ | customer/urls.py → CustomerListCreateView (create) | ✅ |

## 6. Locations & Employees

| Frontend Call | Full URL | Backend Route | Status |
|---------------|----------|---------------|--------|
| `api.get('locations-admin/')` | GET /api/locations-admin/ | inventory/urls.py → LocationViewSet list | ✅ |
| `api.get('sites-admin/')` | GET /api/sites-admin/ | inventory/urls.py → SiteViewSet list | ✅ |
| `api.post('locations-admin/', payload)` | POST /api/locations-admin/ | inventory/urls.py → LocationViewSet | ✅ |
| `api.patch('locations-admin/<id>/', payload)` | PATCH /api/locations-admin/:id/ | inventory/urls.py → LocationViewSet | ✅ |
| `api.delete('locations-admin/<id>/')` | DELETE /api/locations-admin/:id/ | inventory/urls.py → LocationViewSet | ✅ |
| `api.post('sites-admin/', form)` | POST /api/sites-admin/ | inventory/urls.py → SiteViewSet | ✅ |
| `api.patch('sites-admin/<id>/', form)` | PATCH /api/sites-admin/:id/ | inventory/urls.py → SiteViewSet | ✅ |
| `api.delete('sites-admin/<id>/')` | DELETE /api/sites-admin/:id/ | inventory/urls.py → SiteViewSet | ✅ |
| `api.get('core/employees/')` | GET /api/core/employees/ | core/urls.py → EmployeeViewSet list | ✅ |
| `api.post('core/employees/', payload)` | POST /api/core/employees/ | core/urls.py → EmployeeViewSet | ✅ |
| `api.patch('core/employees/<id>/', payload)` | PATCH /api/core/employees/:id/ | core/urls.py → EmployeeViewSet | ✅ |
| `api.delete('core/employees/<id>/')` | DELETE /api/core/employees/:id/ | core/urls.py → EmployeeViewSet | ✅ |
| `api.get('core/roles/')` | GET /api/core/roles/ | core/urls.py → RoleViewSet list | ✅ |
| `api.patch('core/roles/<id>/', form)` | PATCH /api/core/roles/:id/ | core/urls.py → RoleViewSet | ✅ |
| `api.post('core/roles/', form)` | POST /api/core/roles/ | core/urls.py → RoleViewSet | ✅ |
| `api.delete('core/roles/<id>/')` | DELETE /api/core/roles/:id/ | core/urls.py → RoleViewSet | ✅ |

## 7. AI & Dashboard

| Frontend Call | Full URL | Backend Route | Status |
|---------------|----------|---------------|--------|
| `api.get('ai/insights/')` | GET /api/ai/insights/ | ai/urls.py → SmartInsightsView | ✅ |
| `api.get('dashboard/analytics/', { params })` | GET /api/dashboard/analytics/ | inventory/urls.py → DashboardAnalyticsView | ✅ |
| `api.post('ai/sale-auto-tips/', { product_ids, product_names })` | POST /api/ai/sale-auto-tips/ | ai/urls.py → SaleAutoTipsView | ✅ |
| `api.post('ai/cross-sell/', { product_ids, max_results })` | POST /api/ai/cross-sell/ | inventory/urls.py → CrossSellSuggestionView | ✅ |
| `api.post('ai/ask/', { question })` | POST /api/ai/ask/ | ai/urls.py → AskView | ✅ |
| `api.get('ai/business-insights/')` | GET /api/ai/business-insights/ | inventory/urls.py → BusinessInsightView | ✅ |
| `api.get('ai/stock-prediction/', { params })` | GET /api/ai/stock-prediction/ | inventory/urls.py → StockPredictionView | ✅ |
| `api.post('products/ai-suggest/', ...)` | POST /api/products/ai-suggest/ | inventory/urls.py → AIProductSuggestionView | ✅ |

## 8. Inventory & Movements

| Frontend Call | Full URL | Backend Route | Status |
|---------------|----------|---------------|--------|
| `api.post('movements/inbound/', ...)` | POST /api/movements/inbound/ | inventory/urls.py → InventoryInboundView | ✅ |
| `api.post('movements/transfer/', ...)` | POST /api/movements/transfer/ | inventory/urls.py → InventoryTransferView | ✅ |
| `api.get('serials/lookup/', { params })` | GET /api/serials/lookup/ | inventory/urls.py → SerialItemLookupView | ✅ |

## 9. Admin & Reports

| Frontend Call | Full URL | Backend Route | Status |
|---------------|----------|---------------|--------|
| `api.get('admin/pending/')` | GET /api/admin/pending/ | inventory/urls.py → PendingApprovalListView | ✅ |
| `api.patch('admin/approve/<id>/', ...)` | PATCH /api/admin/approve/:id/ | inventory/urls.py → AdminApprovalView | ✅ |

## 10. Notifications

| Frontend Call | Full URL | Backend Route | Status |
|---------------|----------|---------------|--------|
| `api.get('notifications/')` | GET /api/notifications/ | inventory/urls.py → NotificationListView | ✅ |
| `api.patch('notifications/<id>/read/', { is_read: true })` | PATCH /api/notifications/:id/read/ | inventory/urls.py → NotificationMarkAsReadView | ✅ |
| `api.post('notifications/mark-all-read/', {})` | POST /api/notifications/mark-all-read/ | inventory/urls.py → MarkAllAsReadView | ✅ |

## 11. Service (Repairs)

| Frontend Call | Full URL | Backend Route | Status |
|---------------|----------|---------------|--------|
| `api.get('service/repairs/')` | GET /api/service/repairs/ | service/urls.py → RepairServiceViewSet list | ✅ |
| `api.get('service/repairs/<id>/')` | GET /api/service/repairs/:id/ | service/urls.py → RepairServiceViewSet retrieve | ✅ |
| `api.post('service/repairs/', form)` | POST /api/service/repairs/ | service/urls.py → RepairServiceViewSet create | ✅ |
| `api.get('service/repairs/<id>/spare-parts/')` | GET /api/service/repairs/:id/spare-parts/ | service ViewSet nested or action | ✅ |
| `api.post('service/repairs/<id>/spare-parts/', ...)` | POST /api/service/repairs/:id/spare-parts/ | service ViewSet | ✅ |
| `api.delete('service/repairs/<id>/spare-parts/<partId>/')` | DELETE /api/service/repairs/:id/spare-parts/:partId/ | service ViewSet | ✅ |
| `api.get('service/track/', { params })` | GET /api/service/track/ | service/urls.py → RepairTrackingView | ✅ |

## 12. Accounting

| Frontend Call | Full URL | Backend Route | Status |
|---------------|----------|---------------|--------|
| `api.get('accounting/expense-categories/')` | GET /api/accounting/expense-categories/ | accounting/urls.py → ExpenseCategoryViewSet list | ✅ |
| `api.get('accounting/expenses/', { params })` | GET /api/accounting/expenses/ | accounting/urls.py → ExpenseViewSet list | ✅ |
| `api.post('accounting/expenses/', form)` | POST /api/accounting/expenses/ | accounting/urls.py → ExpenseViewSet | ✅ |
| `api.put('accounting/expenses/<id>/', form)` | PUT /api/accounting/expenses/:id/ | accounting/urls.py → ExpenseViewSet | ✅ |
| `api.delete('accounting/expenses/<id>/')` | DELETE /api/accounting/expenses/:id/ | accounting/urls.py → ExpenseViewSet | ✅ |
| `api.get('accounting/expense-categories/')` | GET /api/accounting/expense-categories/ | accounting router | ✅ |
| `api.put('accounting/expense-categories/<id>/', form)` | PUT /api/accounting/expense-categories/:id/ | accounting router | ✅ |
| `api.post('accounting/expense-categories/', form)` | POST /api/accounting/expense-categories/ | accounting router | ✅ |
| `api.delete('accounting/expense-categories/<id>/')` | DELETE /api/accounting/expense-categories/:id/ | accounting router | ✅ |
| `api.get('accounting/pnl/summary/', { params })` | GET /api/accounting/pnl/summary/ | accounting/urls.py → PnLSummaryView | ✅ |
| `api.get('accounting/pnl/profit-from-sales/', { params })` | GET /api/accounting/pnl/profit-from-sales/ | accounting/urls.py → ProfitFromSalesView | ✅ |
| `api.get('accounting/pnl/margin-analysis/')` | GET /api/accounting/pnl/margin-analysis/ | accounting/urls.py → ProfitMarginAnalysisView | ✅ |
| `api.get('accounting/transactions/', { params })` | GET /api/accounting/transactions/ | accounting/urls.py → TransactionListView | ✅ |

## 13. Installation

| Frontend Call | Full URL | Backend Route | Status |
|---------------|----------|---------------|--------|
| `api.get('installation/dashboard/')` | GET /api/installation/dashboard/ | installation/urls.py → InstallationDashboardView | ✅ |
| `api.patch('installation/jobs/<id>/', { field: value })` | PATCH /api/installation/jobs/:id/ | installation/urls.py → InstallationJobViewSet | ✅ |
| `api.post('installation/jobs/<id>/update-status/', ...)` | POST /api/installation/jobs/:id/update-status/ | installation ViewSet action | ✅ |
| `api.post('installation/jobs/<id>/upload-signature/', formData)` | POST /api/installation/jobs/:id/upload-signature/ | installation ViewSet action | ✅ |

## 14. Warranty & Public

| Frontend Call | Full URL | Backend Route | Status |
|---------------|----------|---------------|--------|
| `api.get('warranty/check/', { params })` | GET /api/warranty/check/ | inventory/urls.py → WarrantyCheckView | ✅ |

---

## Summary

- **Frontend baseURL:** `/api/` (from `config.js` → `API_URL`).
- **Backend:** All API routes under `api/`; inventory routes are under `path('api/', include('inventory.urls'))` so inventory paths are **not** prefixed again (e.g. `staff/items/` in inventory → full path `api/staff/items/`).
- **License:** Handled in api interceptor (403 `license_expired` → redirect to `/license-activate`).
- **Auth:** JWT in `Authorization: Bearer <token>`; 401 → logout and redirect to login.

All listed endpoints are wired and **အဆင်ပြေ** (compatible) as of this document. Run backend and frontend and test critical flows: login → POS → sale request → payment methods → invoice; offline queue → sync; settings business-type and payment methods.
