from django.urls import path
from .views import DashboardKPIView, DashboardChartsView

urlpatterns = [
    path('kpis/', DashboardKPIView.as_view(), name='dashboard_kpis'),
    path('charts/', DashboardChartsView.as_view(), name='dashboard_charts'),
]
