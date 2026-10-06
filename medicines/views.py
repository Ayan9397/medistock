from rest_framework import viewsets, filters
from django.db.models import Q
from .models import Category, Medicine
from .serializers import CategorySerializer, MedicineSerializer, MedicineBatchDetailSerializer
from users.permissions import CanManageInventory

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (CanManageInventory,)

class MedicineViewSet(viewsets.ModelViewSet):
    queryset = Medicine.objects.filter(is_active=True).select_related('category')
    permission_classes = (CanManageInventory,)
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'generic_name', 'brand', 'strength']
    ordering_fields = ['name', 'created_at']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MedicineBatchDetailSerializer
        return MedicineSerializer

    def get_queryset(self):
        qs = Medicine.objects.filter(is_active=True).select_related('category')
        category_id = self.request.query_params.get('category')
        prescription = self.request.query_params.get('prescription_required')
        search_query = self.request.query_params.get('q')

        if category_id:
            qs = qs.filter(category_id=category_id)
        if prescription is not None and prescription != '':
            qs = qs.filter(prescription_required=(prescription.lower() in ['true', '1']))
        if search_query:
            qs = qs.filter(
                Q(name__icontains=search_query) |
                Q(generic_name__icontains=search_query) |
                Q(brand__icontains=search_query)
            )
        return qs
