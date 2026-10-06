from rest_framework import serializers
from django.db import transaction
from django.utils import timezone
from .models import PurchaseOrder, PurchaseItem
from inventory.models import Batch, InventoryAuditLog

class PurchaseItemSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)

    class Meta:
        model = PurchaseItem
        fields = ('id', 'medicine', 'medicine_name', 'ordered_quantity', 'received_quantity', 'unit_cost', 'subtotal')
        read_only_fields = ('id', 'subtotal')

class PurchaseOrderSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    items = PurchaseItemSerializer(many=True, read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = (
            'id', 'po_number', 'supplier', 'supplier_name', 'order_date',
            'status', 'total_amount', 'created_by', 'received_at', 'notes', 'items', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'order_date', 'total_amount', 'received_at')

class PurchaseOrderCreateSerializer(serializers.ModelSerializer):
    items = PurchaseItemSerializer(many=True)

    class Meta:
        model = PurchaseOrder
        fields = ('id', 'po_number', 'supplier', 'notes', 'items')

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        user = self.context['request'].user
        with transaction.atomic():
            po = PurchaseOrder.objects.create(status=PurchaseOrder.Status.ORDERED, created_by=user, **validated_data)
            total = 0
            for item_data in items_data:
                item = PurchaseItem.objects.create(purchase_order=po, **item_data)
                total += item.subtotal
            po.total_amount = total
            po.save(update_fields=['total_amount'])
        return po

class ReceiveItemBatchDataSerializer(serializers.Serializer):
    item_id = serializers.IntegerField(required=True)
    batch_number = serializers.CharField(max_length=100, required=True)
    manufacturing_date = serializers.DateField(required=True)
    expiry_date = serializers.DateField(required=True)
    selling_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    received_quantity = serializers.IntegerField(required=True, min_value=1)

class ReceiveStockSerializer(serializers.Serializer):
    items = ReceiveItemBatchDataSerializer(many=True, required=True)
