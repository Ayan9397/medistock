import pytest
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from medicines.models import Category, Medicine
from inventory.models import Batch
from inventory.services import get_inventory_alerts, get_dead_stock

@pytest.mark.django_db
class TestExpiryAndAlerts:
    def setup_method(self):
        self.category = Category.objects.create(name="General Health")
        self.medicine = Medicine.objects.create(
            name="Test Capsule 250mg",
            generic_name="Generic Test",
            brand="Brand X",
            category=self.category,
            dosage_form=Medicine.DosageForm.CAPSULE,
            strength="250mg",
            reorder_level=20,
            maximum_stock=100
        )

    def test_batch_expiry_classifications(self):
        """Validates all 4 levels of expiry classification specified in requirements."""
        today = timezone.now().date()

        # 1. Expired (expiry_date < today)
        b_expired = Batch.objects.create(
            batch_number="B-EXP",
            medicine=self.medicine,
            manufacturing_date=today - timedelta(days=200),
            expiry_date=today - timedelta(days=5),
            purchase_price=Decimal("10"),
            selling_price=Decimal("15"),
            quantity=10,
            initial_quantity=10
        )
        assert b_expired.expiry_status == 'EXPIRED'
        assert b_expired.is_expired is True

        # 2. Critical (expiry within 7 days)
        b_critical = Batch.objects.create(
            batch_number="B-CRIT",
            medicine=self.medicine,
            manufacturing_date=today - timedelta(days=100),
            expiry_date=today + timedelta(days=3),
            purchase_price=Decimal("10"),
            selling_price=Decimal("15"),
            quantity=10,
            initial_quantity=10
        )
        assert b_critical.expiry_status == 'CRITICAL'
        assert b_critical.is_expired is False

        # 3. Warning (expiry within 30 days)
        b_warning = Batch.objects.create(
            batch_number="B-WARN",
            medicine=self.medicine,
            manufacturing_date=today - timedelta(days=50),
            expiry_date=today + timedelta(days=20),
            purchase_price=Decimal("10"),
            selling_price=Decimal("15"),
            quantity=10,
            initial_quantity=10
        )
        assert b_warning.expiry_status == 'WARNING'

        # 4. Normal (expiry > 30 days)
        b_normal = Batch.objects.create(
            batch_number="B-NORM",
            medicine=self.medicine,
            manufacturing_date=today - timedelta(days=10),
            expiry_date=today + timedelta(days=180),
            purchase_price=Decimal("10"),
            selling_price=Decimal("15"),
            quantity=10,
            initial_quantity=10
        )
        assert b_normal.expiry_status == 'NORMAL'

    def test_low_stock_alert_triggers(self):
        """Current stock <= reorder_level triggers low-stock alert."""
        today = timezone.now().date()
        # Add 10 units (reorder level is 20)
        Batch.objects.create(
            batch_number="B-LOW",
            medicine=self.medicine,
            manufacturing_date=today - timedelta(days=10),
            expiry_date=today + timedelta(days=100),
            purchase_price=Decimal("10"),
            selling_price=Decimal("15"),
            quantity=10,
            initial_quantity=10
        )

        assert self.medicine.total_stock == 10
        assert self.medicine.is_low_stock is True

        alerts = get_inventory_alerts()
        low_items = alerts['low_stock']['items']
        assert any(item['id'] == self.medicine.id for item in low_items)

    def test_overstock_alert_triggers(self):
        """Current stock > maximum_stock triggers overstock alert."""
        today = timezone.now().date()
        # Add 150 units (maximum is 100)
        Batch.objects.create(
            batch_number="B-OVER",
            medicine=self.medicine,
            manufacturing_date=today - timedelta(days=10),
            expiry_date=today + timedelta(days=100),
            purchase_price=Decimal("10"),
            selling_price=Decimal("15"),
            quantity=150,
            initial_quantity=150
        )

        assert self.medicine.total_stock == 150
        assert self.medicine.is_overstock is True

        alerts = get_inventory_alerts()
        over_items = alerts['overstock']['items']
        assert any(item['id'] == self.medicine.id for item in over_items)

