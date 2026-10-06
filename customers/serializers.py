from rest_framework import serializers
from .models import Customer

class CustomerSerializer(serializers.ModelSerializer):
    total_purchases_count = serializers.IntegerField(read_only=True)
    total_spend = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Customer
        fields = (
            'id', 'user', 'name', 'phone', 'email', 'address',
            'notes', 'total_purchases_count', 'total_spend',
            'created_at', 'updated_at'
        )
