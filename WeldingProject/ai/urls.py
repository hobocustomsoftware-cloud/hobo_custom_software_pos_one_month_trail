from django.urls import path
from . import views

urlpatterns = [
    path('best-sellers/', views.BestSellersView.as_view(), name='ai-best-sellers'),
    path('suggest/', views.SuggestUpsellView.as_view(), name='ai-suggest'),
    path('sale-auto-tips/', views.SaleAutoTipsView.as_view(), name='ai-sale-auto-tips'),
    path('ask/', views.AskView.as_view(), name='ai-ask'),
    path('insights/', views.SmartInsightsView.as_view(), name='ai-smart-insights'),
]
