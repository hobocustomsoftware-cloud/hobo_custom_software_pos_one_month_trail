from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from django.utils import timezone
from .models import InstallationJob, InstallationStatusHistory
from .serializers import (
    InstallationJobSerializer,
    InstallationJobCreateSerializer,
    InstallationJobUpdateSerializer,
    InstallationJobListSerializer,
)
from core.permissions import IsAdminOrHigher, IsInventoryManagerOrHigher


class InstallationJobViewSet(viewsets.ModelViewSet):
    """
    Installation Job CRUD operations
    """
    queryset = InstallationJob.objects.select_related(
        'sale_transaction',
        'customer',
        'technician',
        'created_by',
        'signed_off_by'
    ).prefetch_related('status_history').order_by('-created_at')
    
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return InstallationJobCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return InstallationJobUpdateSerializer
        elif self.action == 'list':
            return InstallationJobListSerializer
        return InstallationJobSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by technician if provided
        technician_id = self.request.query_params.get('technician', None)
        if technician_id:
            queryset = queryset.filter(technician_id=technician_id)
        
        # Filter active jobs (not cancelled or signed_off)
        active_only = self.request.query_params.get('active_only', None)
        if active_only == 'true':
            queryset = queryset.exclude(status__in=['cancelled', 'signed_off'])
        
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'], url_path='update-status')
    def update_status(self, request, pk=None):
        """Update installation status"""
        installation = self.get_object()
        new_status = request.data.get('status')
        notes = request.data.get('notes', '')
        
        if not new_status:
            return Response(
                {'error': 'Status is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if new_status not in dict(InstallationJob.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = installation.status
        
        with transaction.atomic():
            installation.status = new_status
            installation.save()
            
            # Create status history
            InstallationStatusHistory.objects.create(
                installation_job=installation,
                old_status=old_status,
                new_status=new_status,
                notes=notes,
                updated_by=request.user
            )
            
            # If completed, sync warranty dates
            if new_status == 'completed':
                sync_warranty_dates(installation)
        
        serializer = self.get_serializer(installation)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='upload-signature')
    def upload_signature(self, request, pk=None):
        """Upload customer signature"""
        installation = self.get_object()
        signature_file = request.FILES.get('signature')
        
        if not signature_file:
            return Response(
                {'error': 'Signature file is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = installation.status
        installation.customer_signature = signature_file
        installation.status = 'signed_off'
        installation.signed_off_at = timezone.now()
        installation.signed_off_by = request.user
        installation.save()
        
        # Create status history
        InstallationStatusHistory.objects.create(
            installation_job=installation,
            old_status=old_status,
            new_status='signed_off',
            notes='Customer signature uploaded',
            updated_by=request.user
        )
        
        serializer = self.get_serializer(installation)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='warranty-sync')
    def warranty_sync(self, request, pk=None):
        """Manually sync warranty dates"""
        installation = self.get_object()
        
        if installation.status != 'completed':
            return Response(
                {'error': 'Installation must be completed to sync warranty'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        synced_count = sync_warranty_dates(installation)
        
        return Response({
            'message': f'Warranty dates synced for {synced_count} serial items',
            'synced_count': synced_count
        })


def sync_warranty_dates(installation):
    """
    Sync warranty start dates for all serial numbers in the sale transaction
    Sets warranty_start_date to today for all serial items when installation is completed
    """
    from inventory.models import SerialItem, WarrantyRecord, SaleItem
    
    sale = installation.sale_transaction
    if not sale or sale.status != 'approved':
        return 0
    
    synced_count = 0
    today = timezone.now().date()
    
    # Get all sale items
    sale_items = SaleItem.objects.filter(sale_transaction=sale)
    
    for sale_item in sale_items:
        product = sale_item.product
        
        # Only sync if product has warranty
        if not product.warranty_months or product.warranty_months == 0:
            continue
        
        # Find serial items for this sale
        serial_items = SerialItem.objects.filter(
            sale_transaction=sale,
            product=product,
            status='sold'
        )
        
        for serial_item in serial_items:
            # Calculate warranty end date
            warranty_end_date = None
            if product.warranty_months:
                # Use SerialItem's _add_months method
                warranty_end_date = serial_item._add_months(today, product.warranty_months)
            
            # Update or create warranty record
            warranty_record, created = WarrantyRecord.objects.get_or_create(
                serial_item=serial_item,
                defaults={
                    'product': product,
                    'sale_transaction': sale,
                    'warranty_start_date': today,
                    'warranty_end_date': warranty_end_date
                }
            )
            
            if not created:
                # Update existing warranty record with new start date
                warranty_record.warranty_start_date = today
                warranty_record.warranty_end_date = warranty_end_date
                warranty_record.save()
            
            synced_count += 1
    
    return synced_count


class InstallationDashboardView(APIView):
    """Dashboard view for active installation jobs"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Get active installations (not cancelled or signed_off)
        active_installations = InstallationJob.objects.filter(
            status__in=['pending', 'site_visit', 'in_progress', 'completed']
        ).select_related(
            'sale_transaction',
            'customer',
            'technician'
        ).order_by('-created_at')
        
        serializer = InstallationJobListSerializer(active_installations, many=True)
        
        # Statistics
        stats = {
            'total_active': active_installations.count(),
            'pending': active_installations.filter(status='pending').count(),
            'site_visit': active_installations.filter(status='site_visit').count(),
            'in_progress': active_installations.filter(status='in_progress').count(),
            'completed': active_installations.filter(status='completed').count(),
        }
        
        return Response({
            'installations': serializer.data,
            'statistics': stats
        })
