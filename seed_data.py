import os
import django
from datetime import date, timedelta
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from medicines.models import Category, Medicine
from suppliers.models import Supplier
from inventory.models import Batch, InventoryAuditLog
from customers.models import Customer
from prescriptions.models import Prescription, PrescriptionItem
from purchases.models import PurchaseOrder, PurchaseItem
from sales.models import Sale, SaleItem, SaleItemBatchAllocation

User = get_user_model()

def run_seed():
    print("Seeding MediStock platform with realistic enterprise pharmacy data...")

    # 1. Users & Roles
    admin, _ = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@medistock.com',
            'role': User.Role.ADMIN,
            'first_name': 'Sarah',
            'last_name': 'Connor',
            'is_staff': True,
            'is_superuser': True
        }
    )
    admin.set_password('admin123')
    admin.save()

    pharmacist, _ = User.objects.get_or_create(
        username='pharmacist',
        defaults={
            'email': 'pharma@medistock.com',
            'role': User.Role.PHARMACIST,
            'first_name': 'Dr. Marcus',
            'last_name': 'Vance',
            'phone': '+91 98765 43210'
        }
    )
    pharmacist.set_password('pharma123')
    pharmacist.save()

    inv_manager, _ = User.objects.get_or_create(
        username='inventory',
        defaults={
            'email': 'inv@medistock.com',
            'role': User.Role.INVENTORY_MANAGER,
            'first_name': 'Elena',
            'last_name': 'Rostova',
            'phone': '+91 98765 12345'
        }
    )
    inv_manager.set_password('inv123')
    inv_manager.save()

    customer_user, _ = User.objects.get_or_create(
        username='customer',
        defaults={
            'email': 'john.doe@gmail.com',
            'role': User.Role.CUSTOMER,
            'first_name': 'John',
            'last_name': 'Doe',
            'phone': '+91 91234 56789'
        }
    )
    customer_user.set_password('cust123')
    customer_user.save()

    # 2. Categories
    cat_analgesic, _ = Category.objects.get_or_create(name='Analgesics & Antipyretics', defaults={'description': 'Pain relief and fever reducers'})
    cat_antibiotic, _ = Category.objects.get_or_create(name='Antibiotics', defaults={'description': 'Bacterial infection treatments'})
    cat_cardio, _ = Category.objects.get_or_create(name='Cardiovascular', defaults={'description': 'Heart and blood pressure management'})
    cat_diabetes, _ = Category.objects.get_or_create(name='Diabetes Care', defaults={'description': 'Blood glucose control medicines'})
    cat_gastro, _ = Category.objects.get_or_create(name='Gastrointestinal', defaults={'description': 'Acid reflux, digestion and gut care'})
    cat_respiratory, _ = Category.objects.get_or_create(name='Respiratory', defaults={'description': 'Asthma, bronchitis and cough care'})
    cat_vitamins, _ = Category.objects.get_or_create(name='Vitamins & Supplements', defaults={'description': 'Nutritional supplements'})

    # 3. Suppliers
    sup1, _ = Supplier.objects.get_or_create(
        name='Sun Pharma Distributors',
        defaults={
            'contact_person': 'Rajesh Sharma',
            'email': 'orders@sunpharma-dist.com',
            'phone': '+91 98111 22334',
            'address': 'Plot 42, Okhla Industrial Area Phase III, New Delhi',
            'gst_number': '07AAAAA1234A1Z5',
            'license_number': 'DL-20B-10928'
        }
    )

    sup2, _ = Supplier.objects.get_or_create(
        name='Cipla Healthcare Logistics',
        defaults={
            'contact_person': 'Anita Desai',
            'email': 'supply@cipla-logistics.in',
            'phone': '+91 98222 33445',
            'address': 'GIDC Estate, Makarpura, Vadodara, Gujarat',
            'gst_number': '24BBBBB5678B2Z6',
            'license_number': 'DL-21B-87341'
        }
    )

    sup3, _ = Supplier.objects.get_or_create(
        name="Dr. Reddy's Regional Supply",
        defaults={
            'contact_person': 'Suresh Reddy',
            'email': 'orders@drreddys-reg.com',
            'phone': '+91 98333 44556',
            'address': 'Bollaram Industrial Area, Hyderabad, Telangana',
            'gst_number': '36CCCCC9012C3Z7',
            'license_number': 'DL-20B-55412'
        }
    )

    # 4. Medicines
    med_pcm, _ = Medicine.objects.get_or_create(
        name='Paracetamol 500mg',
        defaults={
            'generic_name': 'Acetaminophen',
            'brand': 'Crocin Advance',
            'category': cat_analgesic,
            'dosage_form': Medicine.DosageForm.TABLET,
            'strength': '500mg',
            'prescription_required': False,
            'description': 'Effective for fever and mild to moderate bodily pain.',
            'reorder_level': 25,
            'maximum_stock': 300
        }
    )

    med_amox, _ = Medicine.objects.get_or_create(
        name='Amoxicillin 500mg',
        defaults={
            'generic_name': 'Amoxicillin Trihydrate',
            'brand': 'Mox 500',
            'category': cat_antibiotic,
            'dosage_form': Medicine.DosageForm.CAPSULE,
            'strength': '500mg',
            'prescription_required': True,
            'description': 'Broad spectrum penicillin antibiotic for bacterial infections.',
            'reorder_level': 20,
            'maximum_stock': 200
        }
    )

    med_azith, _ = Medicine.objects.get_or_create(
        name='Azithromycin 500mg',
        defaults={
            'generic_name': 'Azithromycin',
            'brand': 'Azee 500',
            'category': cat_antibiotic,
            'dosage_form': Medicine.DosageForm.TABLET,
            'strength': '500mg',
            'prescription_required': True,
            'description': 'Macrolide antibiotic for chest infections and pneumonia.',
            'reorder_level': 15,
            'maximum_stock': 150
        }
    )

    med_panto, _ = Medicine.objects.get_or_create(
        name='Pantoprazole 40mg',
        defaults={
            'generic_name': 'Pantoprazole Sodium',
            'brand': 'Pan 40',
            'category': cat_gastro,
            'dosage_form': Medicine.DosageForm.TABLET,
            'strength': '40mg',
            'prescription_required': False,
            'description': 'Proton pump inhibitor that decreases stomach acid production.',
            'reorder_level': 20,
            'maximum_stock': 250
        }
    )

    med_salb, _ = Medicine.objects.get_or_create(
        name='Salbutamol Inhaler 100mcg',
        defaults={
            'generic_name': 'Albuterol / Salbutamol',
            'brand': 'Asthalin',
            'category': cat_respiratory,
            'dosage_form': Medicine.DosageForm.INHALER,
            'strength': '100mcg/puff',
            'prescription_required': True,
            'description': 'Fast-acting bronchodilator for asthma relief.',
            'reorder_level': 10,
            'maximum_stock': 80
        }
    )

    med_vitc, _ = Medicine.objects.get_or_create(
        name='Vitamin C 500mg',
        defaults={
            'generic_name': 'Ascorbic Acid',
            'brand': 'Limcee Chewable',
            'category': cat_vitamins,
            'dosage_form': Medicine.DosageForm.TABLET,
            'strength': '500mg',
            'prescription_required': False,
            'description': 'Essential antioxidant and immune booster chewable tablet.',
            'reorder_level': 40,
            'maximum_stock': 500
        }
    )

    med_amlo, _ = Medicine.objects.get_or_create(
        name='Amlodipine 5mg',
        defaults={
            'generic_name': 'Amlodipine Besylate',
            'brand': 'Amlong 5',
            'category': cat_cardio,
            'dosage_form': Medicine.DosageForm.TABLET,
            'strength': '5mg',
            'prescription_required': True,
            'description': 'Calcium channel blocker for hypertension and angina.',
            'reorder_level': 25,
            'maximum_stock': 300
        }
    )

    # 5. Batches showcasing FEFO logic
    today = date.today()
    Batch.objects.get_or_create(
        batch_number='PCM-2025-A',
        medicine=med_pcm,
        defaults={
            'supplier': sup1,
            'manufacturing_date': today - timedelta(days=120),
            'expiry_date': date(2027, 1, 15),
            'purchase_price': Decimal('1.20'),
            'selling_price': Decimal('2.00'),
            'quantity': 20,
            'initial_quantity': 50,
            'is_active': True
        }
    )

    Batch.objects.get_or_create(
        batch_number='PCM-2025-B',
        medicine=med_pcm,
        defaults={
            'supplier': sup1,
            'manufacturing_date': today - timedelta(days=60),
            'expiry_date': date(2027, 8, 20),
            'purchase_price': Decimal('1.25'),
            'selling_price': Decimal('2.00'),
            'quantity': 50,
            'initial_quantity': 50,
            'is_active': True
        }
    )

    Batch.objects.get_or_create(
        batch_number='PCM-2025-C',
        medicine=med_pcm,
        defaults={
            'supplier': sup2,
            'manufacturing_date': today - timedelta(days=20),
            'expiry_date': date(2027, 12, 10),
            'purchase_price': Decimal('1.30'),
            'selling_price': Decimal('2.00'),
            'quantity': 30,
            'initial_quantity': 30,
            'is_active': True
        }
    )

    # Critical & Warning Batches for Expiry Monitor
    Batch.objects.get_or_create(
        batch_number='PAN-CRIT-04',
        medicine=med_panto,
        defaults={
            'supplier': sup1,
            'manufacturing_date': today - timedelta(days=360),
            'expiry_date': today + timedelta(days=4),
            'purchase_price': Decimal('4.00'),
            'selling_price': Decimal('7.50'),
            'quantity': 15,
            'initial_quantity': 100,
            'is_active': True
        }
    )

    Batch.objects.get_or_create(
        batch_number='SLB-WARN-18',
        medicine=med_salb,
        defaults={
            'supplier': sup2,
            'manufacturing_date': today - timedelta(days=340),
            'expiry_date': today + timedelta(days=18),
            'purchase_price': Decimal('110.00'),
            'selling_price': Decimal('165.00'),
            'quantity': 12,
            'initial_quantity': 50,
            'is_active': True
        }
    )

    Batch.objects.get_or_create(
        batch_number='VTC-EXP-99',
        medicine=med_vitc,
        defaults={
            'supplier': sup3,
            'manufacturing_date': today - timedelta(days=400),
            'expiry_date': today - timedelta(days=25),
            'purchase_price': Decimal('1.50'),
            'selling_price': Decimal('3.00'),
            'quantity': 8,
            'initial_quantity': 100,
            'is_active': True
        }
    )

    # Low stock example: Amlodipine has reorder_level 25, only 5 in stock!
    Batch.objects.get_or_create(
        batch_number='AML-LOW-01',
        medicine=med_amlo,
        defaults={
            'supplier': sup1,
            'manufacturing_date': today - timedelta(days=50),
            'expiry_date': today + timedelta(days=365),
            'purchase_price': Decimal('1.80'),
            'selling_price': Decimal('3.50'),
            'quantity': 5,
            'initial_quantity': 50,
            'is_active': True
        }
    )

    # 6. Customers
    cust1, _ = Customer.objects.get_or_create(
        phone='+91 91234 56789',
        defaults={
            'user': customer_user,
            'name': 'John Doe',
            'email': 'john.doe@gmail.com',
            'address': 'B-12, Green Park Avenue, New Delhi',
            'notes': 'Diabetic patient.'
        }
    )

    print("MediStock database seeded successfully!")

if __name__ == '__main__':
    run_seed()
