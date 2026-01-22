from rest_framework.permissions import BasePermission
from apps.tenants.models import TenantMembership
from .utils import get_tenant_from_request


class HasTenantAccess(BasePermission):
    """
    Exige:
    - header X-Tenant-ID
    - usuário autenticado
    - membership ativo nesse tenant
    """

    message = "Você não tem acesso a este tenant (ou X-Tenant-ID ausente)."

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        try:
            tenant = get_tenant_from_request(request)
        except ValueError:
            return False

        has_membership = TenantMembership.objects.filter(
            tenant=tenant,
            user=request.user,
            is_active=True,
        ).exists()

        if not has_membership:
            return False

        # anexa para o view usar
        request.tenant = tenant
        return True
