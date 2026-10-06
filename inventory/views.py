from rest_framework import viewsets, views, status, permissions, filters
from rest_framework.response import Response
from django.utils import timezone
from .models import Batch, InventoryAuditLog
from .serializers import (
    BatchSerializer,
    BatchCreateUpdateSerializer,
    InventoryAuditLogSerializer,
    FEFOPreviewRequestSerializer
)
from .services import (
    preview_fefo_allocation,
    get_inventory_alerts,
    get_dead_stock,
    InventoryException
)
from users.permissions import CanManageInventory

class BatchViewSet(viewsets.ModelViewSet):
    queryset = Batch.objects.filter(is_active=True).select_related('medicine', 'supplier')
    permission_classes = (CanManageInventory,)
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['batch_number', 'medicine__name', 'supplier__name']
    ordering_fields = ['expiry_date', 'quantity', 'created_at']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return BatchCreateUpdateSerializer
        return BatchSerializer

    def get_queryset(self):
        qs = Batch.objects.filter(is_active=True).select_related('medicine', 'supplier')
        medicine_id = self.request.query_params.get('medicine')
        supplier_id = self.request.query_params.get('supplier')
        status_filter = self.request.query_params.get('status')

        if medicine_id:
            qs = qs.filter(medicine_id=medicine_id)
        if supplier_id:
            qs = qs.filter(supplier_id=supplier_id)

        today = timezone.now().date()
        if status_filter == 'EXPIRED':
            qs = qs.filter(expiry_date__lt=today)
        elif status_filter == 'CRITICAL':
            from datetime import timedelta
            qs = qs.filter(expiry_date__gte=today, expiry_date__lte=today + timedelta(days=7))
        elif status_filter == 'WARNING':
            from datetime import timedelta
            qs = qs.filter(expiry_date__gt=today + timedelta(days=7), expiry_date__lte=today + timedelta(days=30))
        elif status_filter == 'NORMAL':
            from datetime import timedelta
            qs = qs.filter(expiry_date__gt=today + timedelta(days=30))

        return qs

class FEFOPreviewView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = FEFOPreviewRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        med_id = serializer.validated_data['medicine_id']
        qty = serializer.validated_data['quantity']

        try:
            result = preview_fefo_allocation(med_id, qty)
            return Response(result, status=status.HTTP_200_OK)
        except InventoryException as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class StockAlertsView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        data = get_inventory_alerts()
        return Response(data)

class DeadStockView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        days = int(request.query_params.get('days', 60))
        data = get_dead_stock(days=days)
        return Response({'days_threshold': days, 'count': len(data), 'dead_stock': data})

class InventoryAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InventoryAuditLog.objects.all().select_related('medicine', 'batch', 'user')
    serializer_class = InventoryAuditLogSerializer
    permission_classes = (CanManageInventory,)
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['medicine__name', 'batch__batch_number', 'reference']
    ordering_fields = ['created_at']
