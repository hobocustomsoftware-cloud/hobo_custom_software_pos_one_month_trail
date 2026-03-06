from django.urls import path
from .views import LicenseStatusView, LicenseActivateView, RemoteLicenseActivateView

urlpatterns = [
    path('status/', LicenseStatusView.as_view(), name='license-status'),
    path('activate/', LicenseActivateView.as_view(), name='license-activate'),
    path('remote-activate/', RemoteLicenseActivateView.as_view(), name='license-remote-activate'),
]
