from rest_framework import serializers
from .models import InstallationJob, InstallationStatusHistory


class InstallationStatusHistorySerializer(serializers.ModelSerializer):
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)
    
    class Meta:
        model = InstallationStatusHistory
        fields = ['id', 'old_status', 'new_status', 'notes', 'created_at', 'updated_by_username']
        read_only_fields = ['created_at']


class InstallationJobSerializer(serializers.ModelSerializer):
    """Full Installation Job serializer with related data"""
    sale_transaction_invoice = serializers.CharField(source='sale_transaction.invoice_number', read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone_number', read_only=True)
    technician_username = serializers.CharField(source='technician.username', read_only=True)
    technician_name = serializers.SerializerMethodField()
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    signed_off_by_username = serializers.CharField(source='signed_off_by.username', read_only=True)
    status_history = InstallationStatusHistorySerializer(many=True, read_only=True)
    customer_signature_url = serializers.SerializerMethodField()
    
    class Meta:
        model = InstallationJob
        fields = [
            'id',
            'installation_no',
            'sale_transaction',
            'sale_transaction_invoice',
            'customer',
            'customer_name',
            'customer_phone',
            'installation_address',
            'installation_date',
            'estimated_completion_date',
            'site_visit_date',
            'technician',
            'technician_username',
            'technician_name',
            'status',
            'description',
            'notes',
            'customer_signature',
            'customer_signature_url',
            'signed_off_at',
            'signed_off_by',
            'signed_off_by_username',
            'created_at',
            'updated_at',
            'completed_at',
            'created_by',
            'created_by_username',
            'status_history',
        ]
        read_only_fields = [
            'installation_no',
            'created_at',
            'updated_at',
            'completed_at',
            'signed_off_at',
        ]

    def get_technician_name(self, obj):
        if obj.technician:
            return f"{obj.technician.first_name} {obj.technician.last_name}".strip() or obj.technician.username
        return None

    def get_customer_signature_url(self, obj):
        if obj.customer_signature:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.customer_signature.url)
            return obj.customer_signature.url
        return None


class InstallationJobCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Installation Job"""
    
    class Meta:
        model = InstallationJob
        fields = [
            'sale_transaction',
            'installation_address',
            'installation_date',
            'estimated_completion_date',
            'site_visit_date',
            'technician',
            'description',
            'notes',
        ]

    def create(self, validated_data):
        sale_transaction = validated_data.get('sale_transaction')
        
        # Get customer from sale transaction
        customer = sale_transaction.customer if sale_transaction else None
        
        installation = InstallationJob.objects.create(
            sale_transaction=sale_transaction,
            customer=customer,
            created_by=self.context['request'].user,
            **validated_data
        )
        
        # Create initial status history
        InstallationStatusHistory.objects.create(
            installation_job=installation,
            old_status='',
            new_status='pending',
            updated_by=self.context['request'].user
        )
        
        return installation


class InstallationJobUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating Installation Job"""
    
    class Meta:
        model = InstallationJob
        fields = [
            'technician',
            'status',
            'installation_address',
            'installation_date',
            'estimated_completion_date',
            'site_visit_date',
            'description',
            'notes',
            'customer_signature',
        ]

    def update(self, instance, validated_data):
        old_status = instance.status
        new_status = validated_data.get('status', old_status)
        
        # Create status history if status changed
        if old_status != new_status:
            InstallationStatusHistory.objects.create(
                installation_job=instance,
                old_status=old_status,
                new_status=new_status,
                updated_by=self.context['request'].user,
                notes=validated_data.get('notes', '')
            )
        
        return super().update(instance, validated_data)


class InstallationJobListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone_number', read_only=True)
    invoice_number = serializers.CharField(source='sale_transaction.invoice_number', read_only=True)
    technician_username = serializers.CharField(source='technician.username', read_only=True)
    technician_name = serializers.SerializerMethodField()
    
    class Meta:
        model = InstallationJob
        fields = [
            'id',
            'installation_no',
            'invoice_number',
            'customer_name',
            'customer_phone',
            'installation_address',
            'installation_date',
            'estimated_completion_date',
            'site_visit_date',
            'technician_username',
            'technician_name',
            'status',
            'created_at',
            'updated_at',
            'completed_at',
        ]

    def get_technician_name(self, obj):
        if obj.technician:
            return f"{obj.technician.first_name} {obj.technician.last_name}".strip() or obj.technician.username
        return None
