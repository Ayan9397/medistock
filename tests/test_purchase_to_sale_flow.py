import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth import get_user_model
from suppliers.models import Supplier
from medicines.models import Category, Medicine
from purchases.models import PurchaseOrder, PurchaseItem
from inventory.models import Batch, InventoryAuditLog
from sales.models import Sale, SaleItem, SaleItemBatchAllocation
from sales.serializers import CheckoutSaleSerializer

User = get_user_model()

@pytest.mark.django_db
class TestPurchaseToSaleIntegration:
    """
    Full end-to-end integration test:
    Supplier -> Purchase Order -> Receive Stock -> Batch Created -> FEFO Sale -> Stock Deducted -> Audit Log
    """
    def test_complete_pharmacy_lifecycle(self):
        # 1. Create Staff
        pharmacist = User.objects.create_user(
            username='staff_pharma',
            password='password123',
            role=User.Role.PHARMACIST
        )

        # 2. Setup Category & Medicine
        category = Category.objects.create(name="Antibiotics")
        medicine = Medicine.objects.create(
            name="Ciprofloxacin 500mg",
            generic_name="Ciprofloxacin",
            brand="Ciproglen",
            category=category,
            dosage_form=Medicine.DosageForm.TABLET,
            strength="500mg",
            reorder_level=20
        )
        assert medicine.total_stock == 0

        # 3. Create Supplier & Purchase Order
        supplier = Supplier.objects.create(name="Apex Pharma Ltd", phone="9988776655")
        po = PurchaseOrder.objects.create(
            po_number="PO-TEST-001",
            supplier=supplier,
            created_by=pharmacist,
            status=PurchaseOrder.Status.ORDERED
        )
        po_item = PurchaseItem.objects.create(
            purchase_order=po,
            medicine=medicine,
            ordered_quantity=100,
            unit_cost=Decimal("15.00"),
            subtotal=Decimal("1500.00")
        )

        # 4. Receive Stock into Batch
        today = timezone.now().date()
        batch = Batch.objects.create(
            batch_number="BATCH-CIPRO-101",
            medicine=medicine,
            supplier=supplier,
            manufacturing_date=today - timedelta(days=10),
            expiry_date=today + timedelta(days=365),
            purchase_price=Decimal("15.00"),
            selling_price=Decimal("25.00"),
            quantity=100,
            initial_quantity=100
        )
        po.status = PurchaseOrder.Status.RECEIVED
        po.received_at = timezone.now()
        po.save()

        # Check inventory is updated
        assert medicine.total_stock == 100

        # 5. Sell 30 units at POS
        cart_data = {
            'items': [{'medicine_id': medicine.id, 'quantity': 30}],
            'discount_percentage': Decimal("10.00"),
            'tax_percentage': Decimal("5.00"),
            'payment_method': Sale.PaymentMethod.CASH,
            'customer_name_walkin': 'Robert Smith'
        }

        class MockRequest:
            user = pharmacist

        serializer = CheckoutSaleSerializer(data=cart_data, context={'request': MockRequest()})
        assert serializer.is_valid(), serializer.errors
        sale = serializer.save()

        # 6. Verify Financials
        # 30 units * 25.00 = 750.00 subtotal
        assert sale.subtotal == Decimal("750.00")
        # 10% discount = 75.00
        assert sale.discount_amount == Decimal("75.00")
        # taxable = 675.00; 5% tax = 33.75
        assert sale.tax_amount == Decimal("33.75")
        # total = 675.00 + 33.75 = 708.75
        assert sale.total_amount == Decimal("708.75")

        # 7. Verify Inventory Deduction
        batch.refresh_from_db()
        assert batch.quantity == 70
        assert medicine.total_stock == 70

        # 8. Verify Audit Trail and Batch Allocation
        sale_item = sale.items.first()
        assert sale_item.quantity == 30
        allocation = sale_item.batch_allocations.first()
        assert allocation.batch == batch
        assert allocation.allocated_quantity == 30

        audit_entry = InventoryAuditLog.objects.filter(medicine=medicine, batch=batch).first()
        assert audit_entry is not None
        assert audit_entry.quantity_change == -30
        assert audit_entry.new_quantity == 70

