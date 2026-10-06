from rest_framework import viewsets, filters
from .models import Supplier
from .serializers import SupplierSerializer
from users.permissions import CanManageSuppliers

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = (CanManageSuppliers,)
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'contact_person', 'phone', 'email', 'gst_number']
    ordering_fields = ['name', 'created_at']
