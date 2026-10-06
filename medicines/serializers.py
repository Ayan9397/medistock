from rest_framework import serializers
from .models import Category, Medicine

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'description', 'created_at')

class MedicineSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    total_stock = serializers.IntegerField(read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    is_overstock = serializers.BooleanField(read_only=True)
    standard_selling_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Medicine
        fields = (
            'id', 'name', 'generic_name', 'brand', 'category', 'category_name',
            'dosage_form', 'strength', 'prescription_required', 'description',
            'reorder_level', 'maximum_stock', 'is_active', 'total_stock',
            'is_low_stock', 'is_overstock', 'standard_selling_price',
            'created_at', 'updated_at'
        )

class MedicineBatchDetailSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    total_stock = serializers.IntegerField(read_only=True)
    batches = serializers.SerializerMethodField()

    class Meta:
        model = Medicine
        fields = (
            'id', 'name', 'generic_name', 'brand', 'category', 'category_name',
            'dosage_form', 'strength', 'prescription_required', 'description',
            'reorder_level', 'maximum_stock', 'is_active', 'total_stock',
            'batches', 'created_at', 'updated_at'
        )

    def get_batches(self, obj):
        from inventory.serializers import BatchSerializer
        batches = obj.batches.filter(is_active=True).order_by('expiry_date')
        return BatchSerializer(batches, many=True).data
