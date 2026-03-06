# service/views.py
from rest_framework import viewsets, status, permissions, generics, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from .models import RepairService, RepairSparePart, TreatmentRecord, TreatmentRecordFile
from .serializers import (
    RepairServiceSerializer, RepairSparePartSerializer,
    RepairSparePartCreateSerializer,
    TreatmentRecordSerializer, TreatmentRecordFileSerializer, TreatmentRecordFileCreateSerializer,
)


class RepairServiceViewSet(viewsets.ModelViewSet):
    queryset = RepairService.objects.all().select_related('customer', 'location').order_by('-received_date')
    serializer_class = RepairServiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['repair_no', 'item_name', 'customer__name', 'customer__phone_number']
    ordering_fields = ['received_date', 'repair_no', 'status']
    ordering = ['-received_date']

    def perform_create(self, serializer):
        deposit = self.request.data.get('deposit_amount', 0)
        is_paid = float(deposit) > 0
        data = serializer.validated_data
        # Customer မှာ preferred_branch ရှိပြီး location မပို့ပါက pre-fill လုပ်သည်
        if not data.get('location') and data.get('customer') and data['customer'].preferred_branch:
            data['location'] = data['customer'].preferred_branch
        serializer.save(staff=self.request.user, is_deposit_paid=is_paid)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get', 'post'], url_path='spare-parts')
    def spare_parts(self, request, pk=None):
        """GET: Spare Parts စာရင်း | POST: Spare Part ထည့်ခြင်း"""
        repair = self.get_object()
        if request.method == 'GET':
            parts = repair.spare_parts.all()
            return Response(RepairSparePartSerializer(parts, many=True).data)
        serializer = RepairSparePartCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        part = RepairSparePart.objects.create(repair_service=repair, **serializer.validated_data)
        return Response(RepairSparePartSerializer(part).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path='spare-parts/(?P<part_id>[^/.]+)')
    def remove_spare_part(self, request, pk=None, part_id=None):
        """Spare Part ဖျက်ခြင်း"""
        repair = self.get_object()
        part = repair.spare_parts.filter(id=part_id).first()
        if not part:
            return Response({'error': 'Spare part ရှာမတွေ့ပါ။'}, status=status.HTTP_404_NOT_FOUND)
        part.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'], url_path='cost-breakdown')
    def cost_breakdown(self, request, pk=None):
        """Labour + Parts ခွဲခြားပြသခြင်း"""
        from decimal import Decimal
        repair = self.get_object()
        parts = repair.spare_parts.all()
        parts_total = sum((p.subtotal for p in parts), Decimal('0'))
        return Response({
            'labour_cost': float(repair.labour_cost),
            'parts': [{'part_name': p.part_name, 'quantity': p.quantity, 'unit_price': float(p.unit_price), 'subtotal': float(p.subtotal)} for p in parts],
            'parts_total': float(parts_total),
            'total': float(repair.labour_cost) + float(parts_total),
            'deposit_amount': float(repair.deposit_amount),
            'balance_amount': float(repair.balance_amount)
        })


class RepairTrackingView(APIView):
    """Customer များ repair_no + phone ဖြင့် Status စစ်ဆေးခြင်း (Public - Login မလိုပါ)"""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        repair_no = request.query_params.get('repair_no', '').strip()
        phone = request.query_params.get('phone', '').strip().replace(' ', '')
        if not repair_no or not phone:
            return Response({
                'error': 'repair_no နှင့် phone parameter များ လိုအပ်ပါသည်။'
            }, status=400)
        try:
            repair = RepairService.objects.select_related('customer', 'location').get(
                repair_no__iexact=repair_no,
                customer__phone_number__icontains=phone
            )
        except RepairService.DoesNotExist:
            return Response({
                'found': False,
                'message': 'စက်ပြင်မှတ်တမ်း ရှာမတွေ့ပါ။ Repair No. နှင့် ဖုန်းနံပါတ် မှန်ကန်မှု စစ်ဆေးပါ။'
            }, status=404)
        return Response({
            'found': True,
            'repair_no': repair.repair_no,
            'item_name': repair.item_name,
            'status': repair.status,
            'status_display': repair.get_status_display(),
            'return_date': repair.return_date,
            'total_estimated_cost': float(repair.total_estimated_cost),
            'deposit_amount': float(repair.deposit_amount),
            'balance_amount': float(repair.balance_amount),
            'received_date': repair.received_date,
            'location': repair.location.name if repair.location else None
        })


# ---------- ဆေးခန်း ကုသမှုမှတ်တမ်း (Clinic Treatment Record) ----------
class TreatmentRecordViewSet(viewsets.ModelViewSet):
    """လူနာ ကုသမှုမှတ်တမ်း CRUD + ဓာတ်မှန်/အယ်ထရာဆောင်း ဖိုင်များ"""
    queryset = TreatmentRecord.objects.all().select_related('customer', 'staff').prefetch_related('files').order_by('-created_at')
    serializer_class = TreatmentRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['patient_name', 'condition', 'drug_allergies']
    ordering_fields = ['created_at', 'patient_name']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        serializer.save(staff=self.request.user)

    @action(detail=True, methods=['post'], url_path='upload-file')
    def upload_file(self, request, pk=None):
        """ကုသမှုမှတ်တမ်းတွင် ဓာတ်မှန်/အယ်ထရာဆောင်း ဖိုင်တင်ခြင်း"""
        record = self.get_object()
        f = request.FILES.get('file')
        if not f:
            return Response({'error': 'file is required.'}, status=status.HTTP_400_BAD_REQUEST)
        obj = TreatmentRecordFile.objects.create(
            treatment_record=record,
            file_type=request.data.get('file_type', 'other'),
            file=f,
            caption=request.data.get('caption', ''),
        )
        return Response(TreatmentRecordFileSerializer(obj).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path='files/(?P<file_id>[^/.]+)')
    def delete_file(self, request, pk=None, file_id=None):
        """ကုသမှုဖိုင် ဖျက်ခြင်း"""
        record = self.get_object()
        f = record.files.filter(id=file_id).first()
        if not f:
            return Response({'error': 'File not found.'}, status=status.HTTP_404_NOT_FOUND)
        f.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)