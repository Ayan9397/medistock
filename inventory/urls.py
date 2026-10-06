from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BatchViewSet,
    FEFOPreviewView,
    StockAlertsView,
    DeadStockView,
    InventoryAuditLogViewSet
)

router = DefaultRouter()
router.register(r'batches', BatchViewSet, basename='batch')
router.register(r'logs', InventoryAuditLogViewSet, basename='inventory-log')

urlpatterns = [
    path('fefo-preview/', FEFOPreviewView.as_view(), name='fefo-preview'),
    path('alerts/', StockAlertsView.as_view(), name='stock-alerts'),
    path('dead-stock/', DeadStockView.as_view(), name='dead-stock'),
    path('', include(router.urls)),
]
