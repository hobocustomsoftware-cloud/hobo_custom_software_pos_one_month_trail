from rest_framework import serializers
from .models import Customer

class CustomerSerializer(serializers.ModelSerializer):
    """Customer CRUD အတွက် အသုံးပြုသော Serializer"""
    preferred_branch_name = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = ['id', 'name', 'phone_number', 'email', 'address', 'preferred_branch', 'preferred_branch_name', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_preferred_branch_name(self, obj):
        return obj.preferred_branch.name if obj.preferred_branch else '-'