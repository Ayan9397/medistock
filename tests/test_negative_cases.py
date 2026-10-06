import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from medicines.models import Category, Medicine
from inventory.models import Batch

User = get_user_model()

@pytest.mark.django_db
class TestNegativeScenarios:
    def setup_method(self):
        self.client = APIClient()
        self.pharmacist = User.objects.create_user(
            username='negative_tester',
            password='securepassword',
            role=User.Role.PHARMACIST
        )
        self.customer = User.objects.create_user(
            username='customer_tester',
            password='securepassword',
            role=User.Role.CUSTOMER
        )

        self.category = Category.objects.create(name="Emergency Care")
        self.medicine = Medicine.objects.create(
            name="Epinephrine 1mg/ml",
            generic_name="Epinephrine",
            brand="EpiPen",
            category=self.category,
            dosage_form=Medicine.DosageForm.INJECTION,
            strength="1mg/ml",
            prescription_required=True
        )

    def test_negative_sell_unavailable_stock(self):
        """❌ Attempting to sell more stock than exists returns 400 error."""
        self.client.force_authenticate(user=self.pharmacist)
        payload = {
            'items': [{'medicine_id': self.medicine.id, 'quantity': 100}],
            'customer_name_walkin': 'Emergency Patient'
        }
        response = self.client.post('/api/v1/sales/', payload, format='json')
        assert response.status_code == 400

    def test_negative_sell_expired_batch(self):
        """❌ Batches past expiry date are never sold; sale fails if only expired stock exists."""
        today = timezone.now().date()
        Batch.objects.create(
            batch_number="EXP-999",
            medicine=self.medicine,
            manufacturing_date=today - timedelta(days=500),
            expiry_date=today - timedelta(days=10),  # Expired
            purchase_price=Decimal("100"),
            selling_price=Decimal("200"),
            quantity=50,
            initial_quantity=50
        )
        self.client.force_authenticate(user=self.pharmacist)
        payload = {
            'items': [{'medicine_id': self.medicine.id, 'quantity': 5}],
            'customer_name_walkin': 'Patient'
        }
        response = self.client.post('/api/v1/sales/', payload, format='json')
        assert response.status_code == 400

    def test_negative_negative_or_zero_quantity(self):
        """❌ Negative or zero quantity in sale checkout is rejected."""
        self.client.force_authenticate(user=self.pharmacist)
        payload = {
            'items': [{'medicine_id': self.medicine.id, 'quantity': -5}],
            'customer_name_walkin': 'Patient'
        }
        response = self.client.post('/api/v1/sales/', payload, format='json')
        assert response.status_code == 400

    def test_negative_invalid_medicine_id(self):
        """❌ Non-existent medicine ID returns 400 error."""
        self.client.force_authenticate(user=self.pharmacist)
        payload = {
            'items': [{'medicine_id': 999999, 'quantity': 1}],
            'customer_name_walkin': 'Patient'
        }
        response = self.client.post('/api/v1/sales/', payload, format='json')
        assert response.status_code == 400

    def test_negative_unauthorized_api_access(self):
        """❌ Anonymous requests to protected sales endpoint return 401 Unauthorized."""
        self.client.logout()
        payload = {
            'items': [{'medicine_id': self.medicine.id, 'quantity': 1}]
        }
        response = self.client.post('/api/v1/sales/', payload, format='json')
        assert response.status_code == 401

    def test_negative_role_based_permission_denied(self):
        """❌ Customer role attempting to access staff POS sales endpoint returns 403 Forbidden."""
        self.client.force_authenticate(user=self.customer)
        payload = {
            'items': [{'medicine_id': self.medicine.id, 'quantity': 1}],
            'customer_name_walkin': 'Unauthorized'
        }
        response = self.client.post('/api/v1/sales/', payload, format='json')
        assert response.status_code == 403

    def test_negative_duplicate_batch_number(self):
        """❌ Unique constraint prevents duplicate batch number for same medicine."""
        today = timezone.now().date()
        Batch.objects.create(
            batch_number="DUP-BATCH-01",
            medicine=self.medicine,
            manufacturing_date=today - timedelta(days=20),
            expiry_date=today + timedelta(days=200),
            purchase_price=Decimal("10"),
            selling_price=Decimal("20"),
            quantity=10,
            initial_quantity=10
        )
        with pytest.raises(IntegrityError):
            Batch.objects.create(
                batch_number="DUP-BATCH-01",
                medicine=self.medicine,
                manufacturing_date=today - timedelta(days=20),
                expiry_date=today + timedelta(days=200),
                purchase_price=Decimal("10"),
                selling_price=Decimal("20"),
                quantity=10,
                initial_quantity=10
            )

    def test_negative_rx_required_without_prescription(self):
        """❌ Prescription-required medicine cannot be sold without attaching a valid prescription."""
        today = timezone.now().date()
        Batch.objects.create(
            batch_number="RX-VALID-01",
            medicine=self.medicine,
            manufacturing_date=today - timedelta(days=20),
            expiry_date=today + timedelta(days=200),
            purchase_price=Decimal("10"),
            selling_price=Decimal("20"),
            quantity=50,
            initial_quantity=50
        )
        self.client.force_authenticate(user=self.pharmacist)
        payload = {
            'items': [{'medicine_id': self.medicine.id, 'quantity': 1}],
            'customer_name_walkin': 'Patient Without Rx'
            # prescription_id omitted!
        }
        response = self.client.post('/api/v1/sales/', payload, format='json')
        assert response.status_code == 400
        assert 'prescription' in response.data or 'prescription' in str(response.data)

