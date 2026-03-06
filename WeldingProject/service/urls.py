# service/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RepairServiceViewSet, RepairTrackingView, TreatmentRecordViewSet

router = DefaultRouter()
router.register(r'repairs', RepairServiceViewSet, basename='repair')
router.register(r'treatment-records', TreatmentRecordViewSet, basename='treatment-record')

urlpatterns = [
    path('', include(router.urls)),
    path('track/', RepairTrackingView.as_view(), name='repair-tracking'),
]