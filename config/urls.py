from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView
)
from analytics.views import FrontendAppView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', FrontendAppView.as_view(), name='frontend_app'),

    path('api/v1/auth/', include('users.urls')),
    path('api/v1/medicines/', include('medicines.urls')),
    path('api/v1/inventory/', include('inventory.urls')),
    path('api/v1/suppliers/', include('suppliers.urls')),
    path('api/v1/purchases/', include('purchases.urls')),
    path('api/v1/sales/', include('sales.urls')),
    path('api/v1/prescriptions/', include('prescriptions.urls')),
    path('api/v1/customers/', include('customers.urls')),
    path('api/v1/analytics/', include('analytics.urls')),

    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/v1/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
