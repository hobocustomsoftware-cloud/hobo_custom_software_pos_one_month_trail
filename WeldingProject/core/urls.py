# core/urls.py

from django.urls import path, include
from .views import UserDetailView, EmployeeViewSet, RoleViewSet, ShiftViewSet, SelectLocationView, RegisterView, ForgotPasswordView, ResetPasswordView, ShopSettingsView, DatabaseStatsView, OutletListView, SetDashboardOutletView
from .auth_views import UnifiedLoginView, PhoneLoginView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'shifts', ShiftViewSet, basename='shift')

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('shop-settings/', ShopSettingsView.as_view(), name='shop-settings'),
    path('sre/db-stats/', DatabaseStatsView.as_view(), name='sre-db-stats'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('me/', UserDetailView.as_view(), name='user-me'),
    path('select-location/', SelectLocationView.as_view(), name='select-location'),
    path('outlets/', OutletListView.as_view(), name='outlet-list'),
    path('set-dashboard-outlet/', SetDashboardOutletView.as_view(), name='set-dashboard-outlet'),
    path('auth/login/', UnifiedLoginView.as_view(), name='unified-login'),
    path('auth/phone-login/', PhoneLoginView.as_view(), name='phone-login'),
    path('', include(router.urls)),
]