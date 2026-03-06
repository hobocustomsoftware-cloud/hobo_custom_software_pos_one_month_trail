# customer/urls.py 
from django.urls import path
from .views import CustomerListCreateView, CustomerDetailView, InvoiceDetailView

urlpatterns = [
    # Customer CRUD
    path('', CustomerListCreateView.as_view(), name='customer-list-create'), # /api/customer/
    path('<int:pk>/', CustomerDetailView.as_view(), name='customer-detail'), # /api/customer/123/
    
    # Invoice API
    path('invoice/<int:pk>/', InvoiceDetailView.as_view(), name='sale-invoice-detail'), # /api/customer/invoice/123/
]