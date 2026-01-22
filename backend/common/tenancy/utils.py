import uuid
from apps.tenants.models import Tenant


TENANT_HEADER = "HTTP_X_TENANT_ID"  # Django/DRF expõe headers como HTTP_...


def get_tenant_from_request(request) -> Tenant:
    raw = request.META.get(TENANT_HEADER)
    if not raw:
        raise ValueError("Missing X-Tenant-ID header")

    try:
        tenant_id = uuid.UUID(raw)
    except ValueError as exc:
        raise ValueError("Invalid X-Tenant-ID") from exc

    try:
        return Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist as exc:
        raise ValueError("Tenant not found") from exc
