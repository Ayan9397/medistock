from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Sale
from .serializers import SaleSerializer, CheckoutSaleSerializer
from users.permissions import CanSellMedicine

class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.all().select_related('customer', 'cashier', 'prescription').prefetch_related('items__medicine', 'items__batch_allocations__batch')
    permission_classes = (CanSellMedicine,)
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['invoice_number', 'customer__name', 'customer_name_walkin']
    ordering_fields = ['created_at', 'total_amount']

    def get_serializer_class(self):
        if self.action in ['create', 'checkout']:
            return CheckoutSaleSerializer
        return SaleSerializer

    def create(self, request, *args, **kwargs):
        serializer = CheckoutSaleSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        sale = serializer.save()
        return Response(SaleSerializer(sale).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='invoice')
    def invoice(self, request, pk=None):
        sale = self.get_object()
        return Response(SaleSerializer(sale).data)
