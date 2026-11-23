# customer/views.py (အသစ်ဖန်တီးရန်)
from rest_framework import generics, permissions
from inventory.models import SaleTransaction # Inventory မှ Transaction ကို ယူသုံးသည်
from inventory.serializers import InvoiceSerializer # Inventory မှ Serializer ကို ယူသုံးသည်
from .models import Customer
from .serializers import CustomerSerializer
from rest_framework import filters


class CustomerListCreateView(generics.ListCreateAPIView):
    """Customer အသစ်ဖန်တီးခြင်းနှင့် Customer စာရင်းအားလုံးကို ပြသခြင်း"""
    queryset = Customer.objects.all().order_by('-created_at')

    def get_queryset(self):
        # Customer has no outlet FK: scope via preferred_branch outlet, and
        # via the staff's own sales. Unlinked rows stay owner/manager-only.
        from django.db.models import Q
        from core.outlet_utils import get_request_outlet_id, is_owner
        qs = super().get_queryset()
        outlet_id = get_request_outlet_id(self.request)
        if outlet_id is not None:
            qs = qs.filter(
                Q(preferred_branch__outlet_id=outlet_id)
                | Q(saletransaction__outlet_id=outlet_id)
            ).distinct()
        elif not is_owner(self.request.user):
            user = self.request.user
            qs = qs.filter(saletransaction__staff=user).distinct()
        return qs
    serializer_class = CustomerSerializer
    # Staff များလည်း Customer အသစ်ဖန်တီးနိုင်သည်
    permission_classes = [permissions.IsAuthenticated] 

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'phone_number']
    ordering_fields = ['name', 'phone_number', 'created_at']
    ordering = ['-created_at']

class CustomerDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Customer အချက်အလက်များကို ကြည့်ခြင်း၊ ပြင်ဆင်ခြင်း၊ ဖျက်ခြင်း"""
    queryset = Customer.objects.all()

    def get_queryset(self):
        return CustomerListCreateView(request=self.request, format_kwarg=None).get_queryset()
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated] 
    lookup_field = 'pk'


# ----------------------------------------------------
# Invoice API (outlet-scoped: staff cannot access another outlet's invoice)
# ----------------------------------------------------
from core.outlet_utils import filter_queryset_by_outlet


class InvoiceDetailView(generics.RetrieveAPIView):
    """Invoice/Voucher ထုတ်ရန်အတွက် အသုံးပြုသည့် Approved Sale Transaction အသေးစိတ်"""
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'pk'

    def get_queryset(self):
        return filter_queryset_by_outlet(
            SaleTransaction.objects.filter(status='approved'), self.request
        )
    


