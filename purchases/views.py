from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from .models import PurchaseOrder, PurchaseItem
from .serializers import PurchaseOrderSerializer, PurchaseOrderCreateSerializer, ReceiveStockSerializer
from inventory.models import Batch, InventoryAuditLog
from users.permissions import CanManageInventory

class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.all().select_related('supplier', 'created_by').prefetch_related('items__medicine')
    permission_classes = (CanManageInventory,)
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['po_number', 'supplier__name']
    ordering_fields = ['order_date', 'total_amount']

    def get_serializer_class(self):
        if self.action == 'create':
            return PurchaseOrderCreateSerializer
        return PurchaseOrderSerializer

    @action(detail=True, methods=['post'], url_path='receive')
    def receive_stock(self, request, pk=None):
        po = self.get_object()
        if po.status == PurchaseOrder.Status.RECEIVED:
            return Response({'error': 'Purchase order has already been received.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ReceiveStockSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        items_data = serializer.validated_data['items']

        with transaction.atomic():
            for item_info in items_data:
                po_item = po.items.get(id=item_info['item_id'])
                rec_qty = item_info['received_quantity']
                po_item.received_quantity += rec_qty
                po_item.save(update_fields=['received_quantity'])

                batch, created = Batch.objects.get_or_create(
                    batch_number=item_info['batch_number'],
                    medicine=po_item.medicine,
                    defaults={
                        'supplier': po.supplier,
                        'manufacturing_date': item_info['manufacturing_date'],
                        'expiry_date': item_info['expiry_date'],
                        'purchase_price': po_item.unit_cost,
                        'selling_price': item_info['selling_price'],
                        'quantity': rec_qty,
                        'initial_quantity': rec_qty,
                        'is_active': True,
                    }
                )
                if not created:
                    batch.quantity += rec_qty
                    batch.save(update_fields=['quantity', 'updated_at'])

                InventoryAuditLog.objects.create(
                    medicine=po_item.medicine,
                    batch=batch,
                    action=InventoryAuditLog.Action.PURCHASE_RECEIVE,
                    quantity_change=rec_qty,
                    previous_quantity=batch.quantity - rec_qty,
                    new_quantity=batch.quantity,
                    user=request.user,
                    reference=po.po_number,
                    notes=f"PO {po.po_number}"
                )

            po.status = PurchaseOrder.Status.RECEIVED
            po.received_at = timezone.now()
            po.save(update_fields=['status', 'received_at', 'updated_at'])

        return Response(PurchaseOrderSerializer(po).data, status=status.HTTP_200_OK)
