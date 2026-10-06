from django.db import models
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

class Medicine(models.Model):
    class DosageForm(models.TextChoices):
        TABLET = 'TABLET', 'Tablet'
        CAPSULE = 'CAPSULE', 'Capsule'
        SYRUP = 'SYRUP', 'Syrup'
        INJECTION = 'INJECTION', 'Injection'
        OINTMENT = 'OINTMENT', 'Ointment'
        DROPS = 'DROPS', 'Drops'
        INHALER = 'INHALER', 'Inhaler'
        OTHER = 'OTHER', 'Other'

    name = models.CharField(max_length=200, db_index=True)
    generic_name = models.CharField(max_length=200, db_index=True)
    brand = models.CharField(max_length=150, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='medicines')
    dosage_form = models.CharField(max_length=30, choices=DosageForm.choices, default=DosageForm.TABLET)
    strength = models.CharField(max_length=100)
    prescription_required = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)
    reorder_level = models.PositiveIntegerField(default=10)
    maximum_stock = models.PositiveIntegerField(default=500)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.strength}) - {self.brand}"

    @property
    def total_stock(self):
        today = timezone.now().date()
        valid_batches = self.batches.filter(is_active=True, expiry_date__gt=today)
        return sum(b.quantity for b in valid_batches)

    @property
    def is_low_stock(self):
        return self.total_stock <= self.reorder_level

    @property
    def is_overstock(self):
        return self.total_stock > self.maximum_stock

    @property
    def standard_selling_price(self):
        today = timezone.now().date()
        batch = self.batches.filter(is_active=True, quantity__gt=0, expiry_date__gt=today).order_by('expiry_date').first()
        return batch.selling_price if batch else 0.00
