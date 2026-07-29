from rest_framework.permissions import BasePermission, SAFE_METHODS
from accounts.models import ROLE
class PublicReadOnly(BasePermission):
    def has_permission(self, request, view): return request.method in SAFE_METHODS
class IsAdministratorResponder(BasePermission):
    message="An active, verified Administrator/Responder account is required."
    def has_permission(self, request, view):
        u=request.user
        return bool(u and u.is_authenticated and u.is_active and u.is_verified and u.role==ROLE)
