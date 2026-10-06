from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from .models import Customer
from .serializers import CustomerSerializer
from sales.serializers import SaleSerializer

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'phone', 'email']
    ordering_fields = ['name', 'created_at']

    @action(detail=True, methods=['get'], url_path='history')
    def purchase_history(self, request, pk=None):
        customer = self.get_object()
        sales = customer.sales.all().select_related('cashier').prefetch_related('items__medicine')
        return Response(SaleSerializer(sales, many=True).data)

    @action(detail=True, methods=['get'], url_path='top-medicines')
    def top_medicines(self, request, pk=None):
        customer = self.get_object()
        from sales.models import SaleItem

        top_meds = SaleItem.objects.filter(sale__customer=customer) \
            .values('medicine__id', 'medicine__name', 'medicine__strength', 'medicine__brand') \
            .annotate(total_qty=Sum('quantity'), total_spend=Sum('subtotal')) \
            .order_by('-total_qty')[:10]

        return Response(top_meds)
