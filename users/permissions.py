from rest_framework import permissions

class IsAdminUserRole(permissions.BasePermission):
    """Allows access only to Admin users."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin())

class IsPharmacistOrAdmin(permissions.BasePermission):
    """Allows access to Pharmacists and Admins."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_pharmacist())

class IsInventoryStaffOrAdmin(permissions.BasePermission):
    """Allows access to Inventory Managers and Admins."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_inventory_manager())

class CanSellMedicine(permissions.BasePermission):
    """Allows selling medicines: Admin and Pharmacist."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_pharmacist())

class CanManageInventory(permissions.BasePermission):
    """Full inventory management for Admin and Inventory Manager; Read-only for Pharmacist."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_inventory_manager()

class CanManageSuppliers(permissions.BasePermission):
    """Supplier management: Admin and Inventory Manager."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_inventory_manager()

class IsCustomerUser(permissions.BasePermission):
    """Allows access to Customer users."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_customer())

class IsSelfOrStaff(permissions.BasePermission):
    """Allows users to view/edit their own resources or staff to view/edit."""
    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_admin() or request.user.is_pharmacist():
            return True
        # Check customer/owner linkage
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'customer') and getattr(obj.customer, 'user', None):
            return obj.customer.user == request.user
        return obj == request.user

