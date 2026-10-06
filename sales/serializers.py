import uuid
from decimal import Decimal
from rest_framework import serializers
from django.db import transaction
from django.utils import timezone
from .models import Sale, SaleItem, SaleItemBatchAllocation
from medicines.models import Medicine
from customers.models import Customer
from prescriptions.models import Prescription
from inventory.services import allocate_fefo_stock, InventoryException

class SaleItemBatchAllocationSerializer(serializers.ModelSerializer):
    batch_number = serializers.CharField(source='batch.batch_number', read_only=True)
    expiry_date = serializers.DateField(source='batch.expiry_date', read_only=True)

    class Meta:
        model = SaleItemBatchAllocation
        fields = ('id', 'batch', 'batch_number', 'expiry_date', 'allocated_quantity', 'unit_price', 'subtotal')

class SaleItemSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    batch_allocations = SaleItemBatchAllocationSerializer(many=True, read_only=True)

    class Meta:
        model = SaleItem
        fields = ('id', 'medicine', 'medicine_name', 'quantity', 'unit_price', 'subtotal', 'batch_allocations')

class SaleSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='display_customer_name', read_only=True)
    items = SaleItemSerializer(many=True, read_only=True)

    class Meta:
        model = Sale
        fields = (
            'id', 'invoice_number', 'customer', 'customer_name',
            'customer_name_walkin', 'customer_phone_walkin',
            'subtotal', 'discount_percentage', 'discount_amount',
            'tax_percentage', 'tax_amount', 'total_amount',
            'payment_method', 'payment_status', 'notes',
            'items', 'created_at', 'updated_at'
        )

class CartItemInputSerializer(serializers.Serializer):
    medicine_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(required=True, min_value=1)

class CheckoutSaleSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField(required=False, allow_null=True)
    customer_name_walkin = serializers.CharField(required=False, allow_blank=True, default='')
    customer_phone_walkin = serializers.CharField(required=False, allow_blank=True, default='')
    prescription_id = serializers.IntegerField(required=False, allow_null=True)
    discount_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, default=Decimal('0.00'), min_value=Decimal('0.00'), max_value=Decimal('100.00'))
    tax_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, default=Decimal('5.00'), min_value=Decimal('0.00'))
    payment_method = serializers.ChoiceField(choices=Sale.PaymentMethod.choices, default=Sale.PaymentMethod.CASH)
    notes = serializers.CharField(required=False, allow_blank=True, default='')
    items = CartItemInputSerializer(many=True, required=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Cart cannot be empty.")
        return value

    def create(self, validated_data):
        request = self.context['request']
        cashier = request.user
        customer_id = validated_data.get('customer_id')
        customer = Customer.objects.filter(id=customer_id).first() if customer_id else None
        prescription_id = validated_data.get('prescription_id')
        prescription = Prescription.objects.filter(id=prescription_id).first() if prescription_id else None

        items_data = validated_data['items']
        discount_pct = validated_data.get('discount_percentage', Decimal('0.00'))
        tax_pct = validated_data.get('tax_percentage', Decimal('5.00'))
        payment_method = validated_data.get('payment_method', Sale.PaymentMethod.CASH)
        notes = validated_data.get('notes', '')

        today_str = timezone.now().strftime('%Y%m%d')
        invoice_number = f"INV-{today_str}-{uuid.uuid4().hex[:6].upper()}"

        with transaction.atomic():
            medicines_dict = {}
            for item in items_data:
                med_id = item['medicine_id']
                try:
                    med = Medicine.objects.get(id=med_id, is_active=True)
                except Medicine.DoesNotExist:
                    raise serializers.ValidationError({
                        "items": f"Medicine with ID {med_id} does not exist or is inactive."
                    })
                medicines_dict[med_id] = med

                if med.prescription_required and not prescription:
                    raise serializers.ValidationError({
                        "prescription": f"Medicine '{med.name}' strictly requires a prescription before checkout."
                    })

            sale = Sale.objects.create(
                invoice_number=invoice_number,
                customer=customer,
                customer_name_walkin=validated_data.get('customer_name_walkin', ''),
                customer_phone_walkin=validated_data.get('customer_phone_walkin', ''),
                cashier=cashier,
                prescription=prescription,
                subtotal=Decimal('0.00'),
                discount_percentage=discount_pct,
                discount_amount=Decimal('0.00'),
                tax_percentage=tax_pct,
                tax_amount=Decimal('0.00'),
                total_amount=Decimal('0.00'),
                payment_method=payment_method,
                payment_status=Sale.PaymentStatus.PAID,
                notes=notes
            )

            running_subtotal = Decimal('0.00')

            for item_input in items_data:
                med_id = item_input['medicine_id']
                qty = item_input['quantity']
                med = medicines_dict[med_id]

                try:
                    allocations = allocate_fefo_stock(
                        medicine=med,
                        requested_quantity=qty,
                        user=cashier,
                        reference=invoice_number
                    )
                except InventoryException as err:
                    raise serializers.ValidationError({"stock_error": str(err)})

                item_subtotal = sum(alloc['subtotal'] for alloc in allocations)
                unit_price = item_subtotal / Decimal(str(qty))

                sale_item = SaleItem.objects.create(
                    sale=sale,
                    medicine=med,
                    quantity=qty,
                    unit_price=unit_price,
                    subtotal=item_subtotal
                )

                for alloc in allocations:
                    SaleItemBatchAllocation.objects.create(
                        sale_item=sale_item,
                        batch=alloc['batch'],
                        allocated_quantity=alloc['quantity'],
                        unit_price=alloc['unit_price'],
                        subtotal=alloc['subtotal']
                    )

                running_subtotal += item_subtotal

            discount_amount = (running_subtotal * (discount_pct / Decimal('100.00'))).quantize(Decimal('0.01'))
            amount_after_discount = running_subtotal - discount_amount
            tax_amount = (amount_after_discount * (tax_pct / Decimal('100.00'))).quantize(Decimal('0.01'))
            final_total = (amount_after_discount + tax_amount).quantize(Decimal('0.01'))

            sale.subtotal = running_subtotal
            sale.discount_amount = discount_amount
            sale.tax_amount = tax_amount
            sale.total_amount = final_total
            sale.save(update_fields=['subtotal', 'discount_amount', 'tax_amount', 'total_amount'])

            if prescription and prescription.status != Prescription.Status.DISPENSED:
                prescription.status = Prescription.Status.DISPENSED
                prescription.dispensed_by = cashier
                prescription.save(update_fields=['status', 'dispensed_by', 'updated_at'])

        return sale
