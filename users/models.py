from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrator'
        PHARMACIST = 'PHARMACIST', 'Pharmacist'
        INVENTORY_MANAGER = 'INVENTORY_MANAGER', 'Inventory Manager'
        CUSTOMER = 'CUSTOMER', 'Customer'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.PHARMACIST,
        help_text="Role determining application permissions"
    )
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    def is_pharmacist(self):
        return self.role in [self.Role.ADMIN, self.Role.PHARMACIST]

    def is_inventory_manager(self):
        return self.role in [self.Role.ADMIN, self.Role.INVENTORY_MANAGER]

    def is_customer(self):
        return self.role == self.Role.CUSTOMER

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

