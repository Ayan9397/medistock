from django.db import models
from django.utils import timezone
from django.conf import settings
from medicines.models import Medicine
from suppliers.models import Supplier

class Batch(models.Model):
    batch_number = models.CharField(max_length=100, db_index=True)
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='batches')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='batches')
    manufacturing_date = models.DateField()
    expiry_date = models.DateField(db_index=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)
    initial_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['expiry_date', 'created_at']
        verbose_name_plural = 'Batches'
        unique_together = ('batch_number', 'medicine')
        indexes = [
            models.Index(fields=['medicine', 'expiry_date', 'quantity']),
        ]

    def __str__(self):
        return f"{self.medicine.name} | Batch: {self.batch_number} (Exp: {self.expiry_date})"

    @property
    def expiry_status(self):
        today = timezone.now().date()
        if self.expiry_date < today:
            return 'EXPIRED'
        days = (self.expiry_date - today).days
        if days <= 7:
            return 'CRITICAL'
        elif days <= 30:
            return 'WARNING'
        else:
            return 'NORMAL'

    @property
    def days_until_expiry(self):
        today = timezone.now().date()
        return (self.expiry_date - today).days

    @property
    def is_expired(self):
        return self.expiry_date < timezone.now().date()

    @property
    def total_value(self):
        return self.quantity * self.selling_price

class InventoryAuditLog(models.Model):
    class Action(models.TextChoices):
        PURCHASE_RECEIVE = 'PURCHASE_RECEIVE', 'Stock Received'
        SALE_DEDUCTION = 'SALE_DEDUCTION', 'Sale Deduction (FEFO)'
        MANUAL_ADJUSTMENT = 'MANUAL_ADJUSTMENT', 'Manual Adjustment'
        DISPOSAL_EXPIRED = 'DISPOSAL_EXPIRED', 'Disposal of Expired Stock'
        RETURN_RESTOCK = 'RETURN_RESTOCK', 'Return Restocked'

    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='inventory_logs')
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, null=True, blank=True, related_name='logs')
    action = models.CharField(max_length=30, choices=Action.choices)
    quantity_change = models.IntegerField()
    previous_quantity = models.PositiveIntegerField()
    new_quantity = models.PositiveIntegerField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    reference = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
