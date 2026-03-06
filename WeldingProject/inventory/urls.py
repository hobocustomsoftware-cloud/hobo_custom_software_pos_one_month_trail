# inventory/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router သုံးပြီး ViewSet များကို Register လုပ်ခြင်း
router = DefaultRouter()
# Admin များအတွက် CRUD endpoints
router.register(r'categories', views.CategoryViewSet, basename='admin-categories')
router.register(r'products-admin', views.ProductViewSet, basename='admin-products')
router.register(r'product-specifications', views.ProductSpecificationViewSet, basename='product-specifications')
router.register(r'sites-admin', views.SiteViewSet, basename='admin-sites')
router.register(r'locations-admin', views.LocationViewSet, basename='admin-locations')
router.register(r'payment-methods', views.PaymentMethodViewSet, basename='payment-methods')
router.register(r'discount-rules', views.DiscountRuleViewSet, basename='discount-rules')
router.register(r'modifier-groups', views.ModifierGroupViewSet, basename='modifier-groups')
router.register(r'bundles', views.BundleViewSet, basename='bundles')

urlpatterns = [
    # Must be before router so /bundles/validate/ is not matched as pk
    path('bundles/validate/', views.ValidateBundleView.as_view(), name='bundles-validate'),
    # ----------------------------------------------------
    # 1. Router-based URLs (Category, Product Admin, Locations Admin)
    # ----------------------------------------------------
    path('', include(router.urls)),

    # ----------------------------------------------------
    # 2. Staff / POS APIs
    # ----------------------------------------------------
    # ဝန်ထမ်းများ ပစ္စည်းစာရင်းနှင့် Stock ကြည့်ရန် (with + without trailing slash to avoid 404)
    path('staff/items/', views.ProductListAPIView.as_view(), name='staff-product-list'),
    path('staff/items', views.ProductListAPIView.as_view(), name='staff-product-list-no-slash'),
    
    # အရောင်း Request တင်ရန်နှင့် History ကြည့်ရန်
    path('sales/request/', views.SaleRequestCreateView.as_view(), name='sale-request'),
    path('sales/history/', views.StaffSaleHistoryListView.as_view(), name='staff-sale-history'),
    
    # ဝန်ထမ်း၏ ယနေ့အရောင်း Summary
    path('staff/my-sales-summary/', views.StaffSalesSummaryView.as_view(), name='staff-sales-summary'),
    
    # Dropdown များအတွက် Location List
    path('locations/', views.LocationListAPIView.as_view(), name='location-list'),

    # ----------------------------------------------------
    # 3. Admin / Management APIs
    # ----------------------------------------------------
    # အရောင်း Request များ အတည်ပြုရန်/ငြင်းပယ်ရန်
    path('admin/pending/', views.PendingApprovalListView.as_view(), name='admin-pending-list'),
    path('admin/approve/<int:pk>/', views.AdminApprovalView.as_view(), name='admin-approve-reject'),
    
    # Reports & Dashboards
    path('admin/report/daily-summary/', views.DailySalesSummaryView.as_view(), name='admin-daily-summary'),
    path('admin/report/full-inventory/', views.FullInventoryReportView.as_view(), name='admin-full-inventory-report'),
    path('admin/report/low-stock/', views.LowStockReportView.as_view(), name='admin-low-stock-report'),
    path('admin/report/sales-period-summary/', views.SalesSummaryReportView.as_view(), name='sales-summary-report'),
    path('owner-dashboard/', views.OwnerDashboardView.as_view(), name='owner-dashboard'),

    # ----------------------------------------------------
    # 4. Inventory Movements (Stock In/Out Logs)
    # ----------------------------------------------------
    path('movements/', views.InventoryMovementListView.as_view(), name='movement-list'),
    # path('movements/create/', views.InventoryMovementCreateView.as_view(), name='movement-create'),
    path('movements/transfer/', views.InventoryTransferView.as_view(), name='inventory-transfer'),
    path('movements/inbound/', views.InventoryInboundView.as_view(), name='inventory-inbound'),
    path('stock-count/', views.StockCountSubmitView.as_view(), name='stock-count-submit'),
    path('purchases/', views.PurchaseListView.as_view(), name='purchase-list'),
    path('purchases/create/', views.PurchaseCreateView.as_view(), name='purchase-create'),
    path('units/', views.UnitListView.as_view(), name='unit-list'),

    # ----------------------------------------------------
    # 5. Invoices & Vouchers
    # ----------------------------------------------------
    path('invoices/', views.InvoiceListView.as_view(), name='invoice-list'),
    path('invoice/<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice-detail'),
    path('invoice/<int:pk>/pdf/', views.InvoicePDFView.as_view(), name='invoice-pdf'),
    path('invoice/<int:pk>/cancel/', views.InvoiceCancelView.as_view(), name='invoice-cancel'),

    # ----------------------------------------------------
    # 6. Notifications (Real-time & List)
    # ----------------------------------------------------
    path('notifications/', views.NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:pk>/read/', views.NotificationMarkAsReadView.as_view(), name='notification-mark-read'),
    path('notifications/unread-count/', views.UnreadNotificationCountView.as_view(), name='unread-count'),
    path('notifications/mark-all-read/', views.MarkAllAsReadView.as_view(), name='mark-all-read'),

    path('products/lookup/', views.ProductLookupBySkuView.as_view(), name='product-lookup-sku'),
    path('products/search/', views.ProductSearchView.as_view(), name='product-search'),
    path('products/import/preview/', views.ProductImportPreviewView.as_view(), name='product-import-preview'),
    path('products/import/', views.ProductBulkImportView.as_view(), name='product-bulk-import'),
    path('products/<int:pk>/clone/', views.ProductCloneView.as_view(), name='product-clone'),
    path('products/ai-suggest/', views.AIProductSuggestionView.as_view(), name='ai-product-suggest'),
    path('ai/cross-sell/', views.CrossSellSuggestionView.as_view(), name='ai-cross-sell'),
    path('ai/business-insights/', views.BusinessInsightView.as_view(), name='ai-business-insights'),
    path('ai/stock-prediction/', views.StockPredictionView.as_view(), name='ai-stock-prediction'),
    path('admin/sync-prices/', views.SyncPricesView.as_view(), name='admin-sync-prices'),
    path('settings/exchange-rate/', views.GlobalSettingExchangeRateView.as_view(), name='settings-exchange-rate'),
    path('settings/business-type/', views.BusinessTypeSettingView.as_view(), name='settings-business-type'),
    path('settings/service-installation/', views.ServiceInstallationSettingView.as_view(), name='settings-service-installation'),
    path('settings/product-fields/', views.ProductFieldSettingsView.as_view(), name='settings-product-fields'),
    path('settings/exchange-rate/history/', views.ExchangeRateHistoryView.as_view(), name='exchange-rate-history'),
    path('settings/exchange-rate/fetch/', views.ExchangeRateFetchView.as_view(), name='exchange-rate-fetch'),
    path('settings/exchange-rate/adjustments/', views.ExchangeRateAdjustmentsView.as_view(), name='exchange-rate-adjustments'),
    path('serials/lookup/', views.SerialItemLookupView.as_view()),
    path('serials/<int:pk>/', views.SerialItemUpdateView.as_view(), name='serial-item-update'),
    path('serials/<int:serial_id>/history/', views.SerialNumberHistoryView.as_view(), name='serial-history'),

    # ----------------------------------------------------
    # 8. Warranty APIs
    # ----------------------------------------------------
    path('warranty/check/', views.WarrantyCheckView.as_view(), name='warranty-check'),
    path('warranty/expiring-soon/', views.WarrantyExpiringSoonView.as_view(), name='warranty-expiring-soon'),

    # -------------------------------------------------------
    # 7. Other Dashboard AliasProperty
    # -------------------------------------------------------
    path('dashboard/analytics/', views.DashboardAnalyticsView.as_view(), name='dashboard-analytics'),


    path('inventory/management/', views.InventoryManagementAPIView.as_view(), name='inventory-dashboard'),
    
    # ----------------------------------------------------
    # 9. Payment Methods & Payment Proof
    # ----------------------------------------------------
    path('payment-methods/list/', views.PaymentMethodListAPIView.as_view(), name='payment-methods-list'),
    path('sales/<int:pk>/upload-payment-proof/', views.PaymentProofUploadView.as_view(), name='upload-payment-proof'),
    path('sales/<int:pk>/payment-status/', views.PaymentStatusUpdateView.as_view(), name='update-payment-status'),
]