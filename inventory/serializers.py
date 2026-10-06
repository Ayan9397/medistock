from rest_framework import serializers
from .models import Batch, InventoryAuditLog

class BatchSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True, allow_null=True)
    expiry_status = serializers.CharField(read_only=True)
    days_until_expiry = serializers.IntegerField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    total_value = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Batch
        fields = (
            'id', 'batch_number', 'medicine', 'medicine_name', 'supplier',
            'supplier_name', 'manufacturing_date', 'expiry_date',
            'purchase_price', 'selling_price', 'quantity', 'initial_quantity',
            'expiry_status', 'days_until_expiry', 'is_expired', 'total_value',
            'is_active', 'created_at', 'updated_at'
        )

class BatchCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Batch
        fields = (
            'id', 'batch_number', 'medicine', 'supplier',
            'manufacturing_date', 'expiry_date',
            'purchase_price', 'selling_price', 'quantity', 'initial_quantity',
            'is_active'
        )

class InventoryAuditLogSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    batch_number = serializers.CharField(source='batch.batch_number', read_only=True, allow_null=True)
    user_name = serializers.CharField(source='user.username', read_only=True, allow_null=True)

    class Meta:
        model = InventoryAuditLog
        fields = (
            'id', 'medicine', 'medicine_name', 'batch', 'batch_number',
            'action', 'quantity_change', 'previous_quantity', 'new_quantity',
            'user', 'user_name', 'reference', 'notes', 'created_at'
        )

class FEFOPreviewRequestSerializer(serializers.Serializer):
    medicine_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(required=True, min_value=1)
