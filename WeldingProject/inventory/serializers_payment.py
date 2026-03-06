"""
Payment Method Serializers
"""
from rest_framework import serializers
from .models import PaymentMethod, SaleTransaction


class PaymentMethodSerializer(serializers.ModelSerializer):
    qr_code_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'name', 'qr_code_image', 'qr_code_url',
            'account_name', 'account_number', 'is_active',
            'display_order', 'created_at'
        ]
        read_only_fields = ['created_at']
    
    def get_qr_code_url(self, obj):
        if not obj.qr_code_image:
            return None
        try:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.qr_code_image.url)
            return obj.qr_code_image.url
        except Exception:
            return None


class PaymentProofUploadSerializer(serializers.Serializer):
    """Serializer for uploading payment proof screenshot"""
    payment_proof = serializers.ImageField(required=True)
    payment_status = serializers.ChoiceField(
        choices=['paid', 'failed'],
        default='paid',
        required=False
    )


class PaymentStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating payment status"""
    payment_status = serializers.ChoiceField(
        choices=['pending', 'paid', 'failed', 'cash'],
        required=True
    )
