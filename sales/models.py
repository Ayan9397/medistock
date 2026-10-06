from django.db import models
from django.conf import settings
from medicines.models import Medicine
from inventory.models import Batch

class Sale(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH = 'CASH', 'Cash'
        CARD = 'CARD', 'Credit / Debit Card'
        UPI = 'UPI', 'UPI / QR Code'
        NET_BANKING = 'NET_BANKING', 'Net Banking'

    class PaymentStatus(models.TextChoices):
        PAID = 'PAID', 'Paid'
        PENDING = 'PENDING', 'Pending'
        REFUNDED = 'REFUNDED', 'Refunded'

    invoice_number = models.CharField(max_length=50, unique=True, db_index=True)
    customer = models.ForeignKey('customers.Customer', on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    customer_name_walkin = models.CharField(max_length=150, blank=True, null=True)
    customer_phone_walkin = models.CharField(max_length=20, blank=True, null=True)
    cashier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='conducted_sales')
    prescription = models.ForeignKey('prescriptions.Prescription', on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')

    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)

    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.CASH)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PAID)
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.invoice_number} | ₹{self.total_amount}"

    @property
    def display_customer_name(self):
        if self.customer:
            return self.customer.name
        return self.customer_name_walkin or 'Walk-in Customer'

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT, related_name='sale_items')
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ['id']

class SaleItemBatchAllocation(models.Model):
    sale_item = models.ForeignKey(SaleItem, on_delete=models.CASCADE, related_name='batch_allocations')
    batch = models.ForeignKey(Batch, on_delete=models.PROTECT, related_name='sale_allocations')
    allocated_quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
