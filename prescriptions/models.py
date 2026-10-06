import uuid
from django.db import models
from django.conf import settings
from medicines.models import Medicine

class Prescription(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Review'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
        APPROVED = 'APPROVED', 'Approved for Dispensing'
        DISPENSED = 'DISPENSED', 'Dispensed'
        REJECTED = 'REJECTED', 'Rejected'

    prescription_number = models.CharField(max_length=50, unique=True, db_index=True)
    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE, related_name='prescriptions')
    doctor_name = models.CharField(max_length=150)
    doctor_license = models.CharField(max_length=100, blank=True, null=True)
    image = models.FileField(upload_to='prescriptions/%Y/%m/', blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)

    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_prescriptions')
    dispensed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='dispensed_prescriptions')
    rejection_reason = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.prescription_number} - {self.customer.name}"

    def save(self, *args, **kwargs):
        if not self.prescription_number:
            self.prescription_number = f"RX-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT, related_name='prescription_items')
    dosage_instructions = models.CharField(max_length=200)
    quantity_prescribed = models.PositiveIntegerField()
    quantity_dispensed = models.PositiveIntegerField(default=0)
