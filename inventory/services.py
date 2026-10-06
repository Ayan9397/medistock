from datetime import timedelta
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum, Q
from .models import Batch, InventoryAuditLog
from medicines.models import Medicine

class InventoryException(Exception):
    pass

class InsufficientStockError(InventoryException):
    pass

class InvalidQuantityError(InventoryException):
    pass

class ExpiredMedicineError(InventoryException):
    pass

def preview_fefo_allocation(medicine_id, requested_quantity):
    if requested_quantity <= 0:
        raise InvalidQuantityError("Requested quantity must be greater than zero.")

    try:
        medicine = Medicine.objects.get(id=medicine_id, is_active=True)
    except Medicine.DoesNotExist:
        raise InventoryException("Medicine not found or inactive.")

    today = timezone.now().date()
    valid_batches = Batch.objects.filter(
        medicine=medicine,
        is_active=True,
        quantity__gt=0,
        expiry_date__gt=today
    ).order_by('expiry_date', 'id')

    total_available = sum(b.quantity for b in valid_batches)
    if total_available < requested_quantity:
        raise InsufficientStockError(
            f"Insufficient stock for {medicine.name}. Required: {requested_quantity}, Available: {total_available}"
        )

    allocations = []
    remaining_to_allocate = requested_quantity

    for batch in valid_batches:
        if remaining_to_allocate <= 0:
            break
        
        take = min(batch.quantity, remaining_to_allocate)
        allocations.append({
            'batch_id': batch.id,
            'batch_number': batch.batch_number,
            'expiry_date': str(batch.expiry_date),
            'quantity': take,
            'unit_price': float(batch.selling_price),
            'subtotal': float(batch.selling_price * take),
            'days_until_expiry': batch.days_until_expiry,
            'status': batch.expiry_status
        })
        remaining_to_allocate -= take

    return {
        'medicine_id': medicine.id,
        'medicine_name': medicine.name,
        'requested_quantity': requested_quantity,
        'allocations': allocations,
        'estimated_total': sum(a['subtotal'] for a in allocations)
    }

def allocate_fefo_stock(medicine, requested_quantity, user=None, reference=None):
    if requested_quantity <= 0:
        raise InvalidQuantityError("Requested quantity must be positive.")

    today = timezone.now().date()

    valid_batches = list(Batch.objects.select_for_update().filter(
        medicine=medicine,
        is_active=True,
        quantity__gt=0,
        expiry_date__gt=today
    ).order_by('expiry_date', 'id'))

    total_available = sum(b.quantity for b in valid_batches)
    if total_available < requested_quantity:
        raise InsufficientStockError(
            f"Stock deficit for '{medicine.name}'. Available: {total_available}, Requested: {requested_quantity}"
        )

    deductions = []
    remaining_qty = requested_quantity

    for batch in valid_batches:
        if remaining_qty <= 0:
            break

        take_qty = min(batch.quantity, remaining_qty)
        previous_qty = batch.quantity
        new_qty = previous_qty - take_qty
        
        batch.quantity = new_qty
        batch.save(update_fields=['quantity', 'updated_at'])

        InventoryAuditLog.objects.create(
            medicine=medicine,
            batch=batch,
            action=InventoryAuditLog.Action.SALE_DEDUCTION,
            quantity_change=-take_qty,
            previous_quantity=previous_qty,
            new_quantity=new_qty,
            user=user,
            reference=reference,
            notes=f"FEFO allocation for {medicine.name} (Batch {batch.batch_number})"
        )

        deductions.append({
            'batch': batch,
            'batch_id': batch.id,
            'batch_number': batch.batch_number,
            'quantity': take_qty,
            'unit_price': batch.selling_price,
            'subtotal': batch.selling_price * take_qty
        })

        remaining_qty -= take_qty

    return deductions

def get_inventory_alerts():
    today = timezone.now().date()
    seven_days = today + timedelta(days=7)
    thirty_days = today + timedelta(days=30)

    expired_batches = Batch.objects.filter(is_active=True, quantity__gt=0, expiry_date__lt=today).select_related('medicine')
    critical_batches = Batch.objects.filter(is_active=True, quantity__gt=0, expiry_date__gte=today, expiry_date__lte=seven_days).select_related('medicine')
    warning_batches = Batch.objects.filter(is_active=True, quantity__gt=0, expiry_date__gt=seven_days, expiry_date__lte=thirty_days).select_related('medicine')

    all_medicines = Medicine.objects.filter(is_active=True).prefetch_related('batches')
    low_stock = []
    overstock = []

    for med in all_medicines:
        stock = med.total_stock
        if stock <= med.reorder_level:
            low_stock.append({
                'id': med.id,
                'name': med.name,
                'brand': med.brand,
                'strength': med.strength,
                'current_stock': stock,
                'reorder_level': med.reorder_level,
                'deficit': med.reorder_level - stock
            })
        elif stock > med.maximum_stock:
            overstock.append({
                'id': med.id,
                'name': med.name,
                'brand': med.brand,
                'strength': med.strength,
                'current_stock': stock,
                'maximum_stock': med.maximum_stock,
                'excess': stock - med.maximum_stock
            })

    return {
        'low_stock': {
            'count': len(low_stock),
            'items': low_stock
        },
        'overstock': {
            'count': len(overstock),
            'items': overstock
        },
        'expiry_monitor': {
            'expired_count': expired_batches.count(),
            'critical_count': critical_batches.count(),
            'warning_count': warning_batches.count(),
            'expired_batches': [
                {
                    'id': b.id,
                    'batch_number': b.batch_number,
                    'medicine_id': b.medicine.id,
                    'medicine_name': b.medicine.name,
                    'quantity': b.quantity,
                    'expiry_date': str(b.expiry_date),
                    'days_expired': abs((b.expiry_date - today).days)
                } for b in expired_batches[:50]
            ],
            'critical_batches': [
                {
                    'id': b.id,
                    'batch_number': b.batch_number,
                    'medicine_id': b.medicine.id,
                    'medicine_name': b.medicine.name,
                    'quantity': b.quantity,
                    'expiry_date': str(b.expiry_date),
                    'days_left': (b.expiry_date - today).days
                } for b in critical_batches[:50]
            ],
            'warning_batches': [
                {
                    'id': b.id,
                    'batch_number': b.batch_number,
                    'medicine_id': b.medicine.id,
                    'medicine_name': b.medicine.name,
                    'quantity': b.quantity,
                    'expiry_date': str(b.expiry_date),
                    'days_left': (b.expiry_date - today).days
                } for b in warning_batches[:50]
            ]
        }
    }

def get_dead_stock(days=60):
    cutoff_date = timezone.now() - timedelta(days=days)
    from sales.models import SaleItem

    active_medicine_ids = SaleItem.objects.filter(
        sale__created_at__gte=cutoff_date
    ).values_list('medicine_id', flat=True).distinct()

    dead_stock_meds = Medicine.objects.filter(
        is_active=True
    ).exclude(
        id__in=active_medicine_ids
    ).prefetch_related('batches')

    result = []
    for med in dead_stock_meds:
        stock = med.total_stock
        if stock > 0:
            result.append({
                'id': med.id,
                'name': med.name,
                'brand': med.brand,
                'category': med.category.name,
                'total_stock': stock,
                'stock_value': float(sum(b.quantity * b.selling_price for b in med.batches.filter(is_active=True, expiry_date__gt=timezone.now().date()))),
                'days_inactive': days
            })

    return sorted(result, key=lambda x: x['stock_value'], reverse=True)
