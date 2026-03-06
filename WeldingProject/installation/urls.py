from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InstallationJobViewSet, InstallationDashboardView

router = DefaultRouter()
router.register(r'jobs', InstallationJobViewSet, basename='installation-job')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', InstallationDashboardView.as_view(), name='installation-dashboard'),
]
