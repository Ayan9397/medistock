from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncDate
from sales.models import Sale, SaleItem
from medicines.models import Medicine
from inventory.models import Batch

def get_kpis():
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    today_date = now.date()

    today_sales_qs = Sale.objects.filter(created_at__gte=today_start)
    today_revenue = today_sales_qs.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    today_orders_count = today_sales_qs.count()

    monthly_sales_qs = Sale.objects.filter(created_at__gte=month_start)
    monthly_revenue = monthly_sales_qs.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    monthly_orders_count = monthly_sales_qs.count()

    overall_aov = monthly_sales_qs.aggregate(avg=Avg('total_amount'))['avg'] or Decimal('0.00')

    total_medicines_count = Medicine.objects.filter(is_active=True).count()
    low_stock_count = 0
    for m in Medicine.objects.filter(is_active=True).prefetch_related('batches'):
        if m.total_stock <= m.reorder_level:
            low_stock_count += 1

    thirty_days_future = today_date + timedelta(days=30)
    seven_days_future = today_date + timedelta(days=7)

    expired_count = Batch.objects.filter(is_active=True, quantity__gt=0, expiry_date__lt=today_date).count()
    critical_count = Batch.objects.filter(is_active=True, quantity__gt=0, expiry_date__gte=today_date, expiry_date__lte=seven_days_future).count()
    expiring_soon_count = Batch.objects.filter(is_active=True, quantity__gt=0, expiry_date__gte=today_date, expiry_date__lte=thirty_days_future).count()

    return {
        'sales_kpis': {
            'today_revenue': float(today_revenue),
            'monthly_revenue': float(monthly_revenue),
            'orders_today': today_orders_count,
            'orders_month': monthly_orders_count,
            'average_order_value': round(float(overall_aov), 2)
        },
        'inventory_kpis': {
            'total_medicines': total_medicines_count,
            'low_stock_count': low_stock_count,
            'critical_expiring_7d': critical_count,
            'expiring_soon_30d': expiring_soon_count,
            'expired_count': expired_count,
            'total_active_batches': Batch.objects.filter(is_active=True, quantity__gt=0).count()
        }
    }

def get_chart_data():
    now = timezone.now()
    fourteen_days_ago = now - timedelta(days=14)
    daily_sales = Sale.objects.filter(created_at__gte=fourteen_days_ago) \
        .annotate(date=TruncDate('created_at')) \
        .values('date') \
        .annotate(revenue=Sum('total_amount'), orders=Count('id')) \
        .order_by('date')

    daily_trend = [
        {
            'date': item['date'].strftime('%Y-%m-%d'),
            'revenue': float(item['revenue'] or 0),
            'orders': item['orders']
        } for item in daily_sales
    ]

    top_medicines = SaleItem.objects \
        .values('medicine__name', 'medicine__strength', 'medicine__category__name') \
        .annotate(total_units=Sum('quantity'), total_revenue=Sum('subtotal')) \
        .order_by('-total_units')[:10]

    top_meds_list = [
        {
            'name': f"{item['medicine__name']} ({item['medicine__strength']})",
            'category': item['medicine__category__name'],
            'units_sold': item['total_units'],
            'revenue': float(item['total_revenue'])
        } for item in top_medicines
    ]

    category_sales = SaleItem.objects \
        .values('medicine__category__name') \
        .annotate(total_revenue=Sum('subtotal'), total_units=Sum('quantity')) \
        .order_by('-total_revenue')

    category_distribution = [
        {
            'category': item['medicine__category__name'] or 'Uncategorized',
            'revenue': float(item['total_revenue']),
            'units': item['total_units']
        } for item in category_sales
    ]

    batches = Batch.objects.filter(is_active=True, quantity__gt=0)
    normal = 0
    warning = 0
    critical = 0
    expired = 0

    for b in batches:
        st = b.expiry_status
        if st == 'EXPIRED':
            expired += 1
        elif st == 'CRITICAL':
            critical += 1
        elif st == 'WARNING':
            warning += 1
        else:
            normal += 1

    expiry_distribution = [
        {'name': 'Normal (> 30 days)', 'count': normal, 'color': '#10B981'},
        {'name': 'Warning (8 - 30 days)', 'count': warning, 'color': '#F59E0B'},
        {'name': 'Critical (<= 7 days)', 'count': critical, 'color': '#EF4444'},
        {'name': 'Expired', 'count': expired, 'color': '#6B7280'}
    ]

    return {
        'daily_trend': daily_trend,
        'top_medicines': top_meds_list,
        'category_distribution': category_distribution,
        'expiry_distribution': expiry_distribution
    }
