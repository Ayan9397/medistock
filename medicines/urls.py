from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, MedicineViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'', MedicineViewSet, basename='medicine')

urlpatterns = [
    path('', include(router.urls)),
]
