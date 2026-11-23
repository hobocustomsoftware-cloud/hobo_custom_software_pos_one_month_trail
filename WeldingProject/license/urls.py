from django.urls import path
from .views import (
    BackupActivateView, BackupStatusView, LicenseActivateView, LicenseStatusView,
    RemoteLicenseActivateView, SubscriptionPlanListView,
)

urlpatterns = [
    path('status/', LicenseStatusView.as_view(), name='license-status'),
    path('activate/', LicenseActivateView.as_view(), name='license-activate'),
    path('remote-activate/', RemoteLicenseActivateView.as_view(), name='license-remote-activate'),
    path('plans/', SubscriptionPlanListView.as_view(), name='license-plans'),
    path('backup/status/', BackupStatusView.as_view(), name='backup-status'),
    path('backup/activate/', BackupActivateView.as_view(), name='backup-activate'),
]
