import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone
from medicines.models import Category, Medicine
from inventory.models import Batch
from inventory.services import (
    allocate_fefo_stock,
    preview_fefo_allocation,
    InsufficientStockError,
    InvalidQuantityError
)

@pytest.mark.django_db
class TestFEFOAlgorithm:
    def setup_method(self):
        self.category = Category.objects.create(name="Analgesics Test", description="Testing")
        self.medicine = Medicine.objects.create(
            name="Paracetamol 500mg Test",
            generic_name="Acetaminophen",
            brand="Panadol",
            category=self.category,
            dosage_form=Medicine.DosageForm.TABLET,
            strength="500mg",
            reorder_level=10,
            maximum_stock=200
        )

        today = timezone.now().date()
        # Batch A: expires Jan 2027 (sooner), 20 units
        self.batch_a = Batch.objects.create(
            batch_number="BATCH-A-2027",
            medicine=self.medicine,
            manufacturing_date=today - timedelta(days=60),
            expiry_date=date(2027, 1, 15),
            purchase_price=Decimal("1.00"),
            selling_price=Decimal("2.00"),
            quantity=20,
            initial_quantity=20
        )
        # Batch B: expires Aug 2027 (later), 50 units
        self.batch_b = Batch.objects.create(
            batch_number="BATCH-B-2027",
            medicine=self.medicine,
            manufacturing_date=today - timedelta(days=30),
            expiry_date=date(2027, 8, 20),
            purchase_price=Decimal("1.10"),
            selling_price=Decimal("2.00"),
            quantity=50,
            initial_quantity=50
        )
        # Batch C: expires Dec 2027 (latest), 30 units
        self.batch_c = Batch.objects.create(
            batch_number="BATCH-C-2027",
            medicine=self.medicine,
            manufacturing_date=today - timedelta(days=10),
            expiry_date=date(2027, 12, 10),
            purchase_price=Decimal("1.20"),
            selling_price=Decimal("2.00"),
            quantity=30,
            initial_quantity=30
        )

    def test_fefo_allocation_exact_example(self):
        """
        Verify the exact business logic example:
        Purchase 25 units:
        Batch A gives 20 (depleted to 0)
        Batch B gives 5 (remaining 45)
        Batch C untouched (remaining 30)
        """
        allocations = allocate_fefo_stock(self.medicine, requested_quantity=25)

        # Assert allocation breakdown
        assert len(allocations) == 2
        assert allocations[0]['batch_id'] == self.batch_a.id
        assert allocations[0]['quantity'] == 20
        assert allocations[1]['batch_id'] == self.batch_b.id
        assert allocations[1]['quantity'] == 5

        # Refresh from database
        self.batch_a.refresh_from_db()
        self.batch_b.refresh_from_db()
        self.batch_c.refresh_from_db()

        assert self.batch_a.quantity == 0
        assert self.batch_b.quantity == 45
        assert self.batch_c.quantity == 30

    def test_fefo_preview_does_not_modify_database(self):
        """Verify preview calculation displays future deduction without mutating database."""
        preview = preview_fefo_allocation(self.medicine.id, requested_quantity=25)
        
        assert len(preview['allocations']) == 2
        assert preview['allocations'][0]['batch_number'] == "BATCH-A-2027"
        assert preview['allocations'][0]['quantity'] == 20
        assert preview['allocations'][1]['batch_number'] == "BATCH-B-2027"
        assert preview['allocations'][1]['quantity'] == 5

        # Verify database was NOT touched
        self.batch_a.refresh_from_db()
        self.batch_b.refresh_from_db()
        assert self.batch_a.quantity == 20
        assert self.batch_b.quantity == 50

    def test_fefo_skips_expired_batches(self):
        """Expired batches must NEVER be allocated to customers."""
        today = timezone.now().date()
        expired_batch = Batch.objects.create(
            batch_number="EXPIRED-BATCH",
            medicine=self.medicine,
            manufacturing_date=today - timedelta(days=400),
            expiry_date=today - timedelta(days=1),  # Expired yesterday
            purchase_price=Decimal("1.00"),
            selling_price=Decimal("2.00"),
            quantity=100,
            initial_quantity=100
        )

        allocations = allocate_fefo_stock(self.medicine, requested_quantity=10)
        # Should allocate from Batch A (valid), ignoring the expired batch even though it was older
        assert allocations[0]['batch_id'] == self.batch_a.id

        expired_batch.refresh_from_db()
        assert expired_batch.quantity == 100  # Untouched

    def test_insufficient_stock_raises_error(self):
        """Requesting more than total valid stock raises InsufficientStockError."""
        # Total available is 20 + 50 + 30 = 100
        with pytest.raises(InsufficientStockError):
            allocate_fefo_stock(self.medicine, requested_quantity=101)

    def test_negative_or_zero_quantity_raises_error(self):
        """Negative or zero quantity throws InvalidQuantityError."""
        with pytest.raises(InvalidQuantityError):
            allocate_fefo_stock(self.medicine, requested_quantity=0)

        with pytest.raises(InvalidQuantityError):
            allocate_fefo_stock(self.medicine, requested_quantity=-5)

