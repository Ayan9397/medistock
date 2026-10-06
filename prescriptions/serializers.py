from rest_framework import serializers
from .models import Prescription, PrescriptionItem

class PrescriptionItemSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)

    class Meta:
        model = PrescriptionItem
        fields = ('id', 'medicine', 'medicine_name', 'dosage_instructions', 'quantity_prescribed', 'quantity_dispensed')

class PrescriptionSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    items = PrescriptionItemSerializer(many=True, read_only=True)

    class Meta:
        model = Prescription
        fields = (
            'id', 'prescription_number', 'customer', 'customer_name',
            'doctor_name', 'doctor_license', 'image', 'notes', 'status',
            'verified_by', 'dispensed_by', 'rejection_reason',
            'items', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'prescription_number', 'verified_by', 'dispensed_by', 'created_at')

class PrescriptionCreateSerializer(serializers.ModelSerializer):
    items = PrescriptionItemSerializer(many=True, required=False)

    class Meta:
        model = Prescription
        fields = ('id', 'customer', 'doctor_name', 'doctor_license', 'image', 'notes', 'items')

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        prescription = Prescription.objects.create(**validated_data)
        for item_data in items_data:
            PrescriptionItem.objects.create(prescription=prescription, **item_data)
        return prescription

class VerifyPrescriptionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['APPROVE', 'REJECT', 'UNDER_REVIEW'])
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
