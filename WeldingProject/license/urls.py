from django.urls import path
from .views import (
    BackupActivateView, BackupStatusView, LicenseActivateView, LicenseStatusView,
    RemoteLicenseActivateView, SubscriptionPlanListView,
    TrialCheckoutApproveView, TrialCheckoutProofView, TrialCheckoutView,
)

urlpatterns = [
    path('status/', LicenseStatusView.as_view(), name='license-status'),
    path('activate/', LicenseActivateView.as_view(), name='license-activate'),
    path('remote-activate/', RemoteLicenseActivateView.as_view(), name='license-remote-activate'),
    path('plans/', SubscriptionPlanListView.as_view(), name='license-plans'),
    path('backup/status/', BackupStatusView.as_view(), name='backup-status'),
    path('backup/activate/', BackupActivateView.as_view(), name='backup-activate'),
    path('checkout/', TrialCheckoutView.as_view(), name='trial-checkout'),
    path('checkout/<int:order_id>/proof/', TrialCheckoutProofView.as_view(), name='trial-checkout-proof'),
    path('checkout/<int:order_id>/approve/', TrialCheckoutApproveView.as_view(), name='trial-checkout-approve'),
]
