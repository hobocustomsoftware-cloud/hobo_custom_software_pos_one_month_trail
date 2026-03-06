from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'expense-categories', views.ExpenseCategoryViewSet, basename='expense-category')
router.register(r'expenses', views.ExpenseViewSet, basename='expense')

urlpatterns = [
    path('', include(router.urls)),
    path('transactions/', views.TransactionListView.as_view(), name='transaction-list'),
    path('pnl/summary/', views.PnLSummaryView.as_view(), name='pnl-summary'),
    path('pnl/profit-from-sales/', views.ProfitFromSalesView.as_view(), name='profit-from-sales'),
    path('pnl/trend/', views.ProfitTrendView.as_view(), name='profit-trend'),
    path('pnl/margin-analysis/', views.ProfitMarginAnalysisView.as_view(), name='profit-margin-analysis'),
    # Owner / AI Agent: တစ်ခါခေါ်ပြီး Sales + P&L summary
    path('owner-summary/', views.OwnerSummaryView.as_view(), name='owner-summary'),
]
