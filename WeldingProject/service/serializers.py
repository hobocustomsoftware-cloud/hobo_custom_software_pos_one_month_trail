from rest_framework import serializers
from .models import RepairService, RepairSparePart, RepairStatusHistory, TreatmentRecord, TreatmentRecordFile
from customer.serializers import CustomerSerializer


class RepairSparePartSerializer(serializers.ModelSerializer):
    class Meta:
        model = RepairSparePart
        fields = ['id', 'product', 'part_name', 'quantity', 'unit_price', 'subtotal']
        read_only_fields = ['subtotal']


class RepairStatusHistorySerializer(serializers.ModelSerializer):
    updated_by_username = serializers.ReadOnlyField(source='updated_by.username')

    class Meta:
        model = RepairStatusHistory
        fields = ['id', 'old_status', 'new_status', 'notes', 'created_at', 'updated_by_username']


class RepairServiceSerializer(serializers.ModelSerializer):
    customer_info = CustomerSerializer(source='customer', read_only=True)
    balance_amount = serializers.ReadOnlyField()
    spare_parts = RepairSparePartSerializer(many=True, read_only=True)
    status_history = RepairStatusHistorySerializer(many=True, read_only=True)
    parts_total = serializers.ReadOnlyField()
    total_cost_breakdown = serializers.ReadOnlyField()

    class Meta:
        model = RepairService
        fields = '__all__'

    def update(self, instance, validated_data):
        old_status = instance.status
        result = super().update(instance, validated_data)
        new_status = validated_data.get('status')
        if new_status and new_status != old_status:
            RepairStatusHistory.objects.create(
                repair_service=instance,
                old_status=old_status,
                new_status=new_status,
                updated_by=self.context.get('request').user if self.context.get('request') else None
            )
        return result


class RepairSparePartCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RepairSparePart
        fields = ['product', 'part_name', 'quantity', 'unit_price']


# ---------- ဆေးခန်း ကုသမှုမှတ်တမ်း ----------
class TreatmentRecordFileSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = TreatmentRecordFile
        fields = ['id', 'file_type', 'file', 'file_url', 'caption', 'created_at']
        read_only_fields = ['created_at']

    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class TreatmentRecordSerializer(serializers.ModelSerializer):
    files = TreatmentRecordFileSerializer(many=True, read_only=True)

    class Meta:
        model = TreatmentRecord
        fields = [
            'id', 'patient_name', 'age', 'condition', 'drug_allergies', 'notes',
            'customer', 'staff', 'created_at', 'updated_at', 'files',
        ]
        read_only_fields = ['created_at', 'updated_at']


class TreatmentRecordFileCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TreatmentRecordFile
        fields = ['treatment_record', 'file_type', 'file', 'caption']