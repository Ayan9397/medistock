import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from medicines.models import Category, Medicine
from inventory.models import Batch
from suppliers.models import Supplier

User = get_user_model()

@pytest.mark.django_db
class TestAPIEndpoints:
    def setup_method(self):
        self.client = APIClient()
        self.pharmacist = User.objects.create_user(
            username='api_pharma_test',
            password='secretpassword',
            role=User.Role.PHARMACIST
        )
        self.client.force_authenticate(user=self.pharmacist)

        self.category = Category.objects.create(name="Dermatology")
        self.medicine = Medicine.objects.create(
            name="Hydrocortisone Cream 1%",
            generic_name="Hydrocortisone",
            brand="Cortizone",
            category=self.category,
            dosage_form=Medicine.DosageForm.OINTMENT,
            strength="1%",
            reorder_level=5
        )
        today = timezone.now().date()
        self.batch = Batch.objects.create(
            batch_number="HYD-001",
            medicine=self.medicine,
            manufacturing_date=today - timedelta(days=20),
            expiry_date=today + timedelta(days=200),
            purchase_price=Decimal("30.00"),
            selling_price=Decimal("50.00"),
            quantity=40,
            initial_quantity=40
        )

    def test_get_inventory_batches(self):
        """GET /api/v1/inventory/batches/ returns active stock."""
        response = self.client.get('/api/v1/inventory/batches/')
        assert response.status_code == 200
        data = response.data.get('results', response.data)
        assert len(data) >= 1
        assert any(b['batch_number'] == 'HYD-001' for b in data)

    def test_post_sales_checkout(self):
        """POST /api/v1/sales/ executes POS checkout transaction."""
        payload = {
            'items': [{'medicine_id': self.medicine.id, 'quantity': 5}],
            'discount_percentage': '0.00',
            'tax_percentage': '5.00',
            'payment_method': 'CASH',
            'customer_name_walkin': 'Jane Doe'
        }
        response = self.client.post('/api/v1/sales/', payload, format='json')
        assert response.status_code == 201
        assert response.data['total_amount'] is not None
        assert response.data['invoice_number'].startswith('INV-')

        # Verify stock decreased by 5
        self.batch.refresh_from_db()
        assert self.batch.quantity == 35

    def test_fefo_preview_api(self):
        """POST /api/v1/inventory/fefo-preview/ simulates batch breakdown."""
        payload = {
            'medicine_id': self.medicine.id,
            'quantity': 10
        }
        response = self.client.post('/api/v1/inventory/fefo-preview/', payload, format='json')
        assert response.status_code == 200
        assert response.data['requested_quantity'] == 10
        assert len(response.data['allocations']) == 1
        assert response.data['allocations'][0]['quantity'] == 10

    def test_alerts_api(self):
        """GET /api/v1/inventory/alerts/ returns system alerts."""
        response = self.client.get('/api/v1/inventory/alerts/')
        assert response.status_code == 200
        assert 'low_stock' in response.data
        assert 'expiry_monitor' in response.data
