from rest_framework import serializers
from .models import Supplier

class SupplierSerializer(serializers.ModelSerializer):
    total_orders = serializers.IntegerField(read_only=True)

    class Meta:
        model = Supplier
        fields = (
            'id', 'name', 'contact_person', 'email', 'phone', 'address',
            'gst_number', 'license_number', 'is_active',
            'total_orders', 'created_at', 'updated_at'
        )
