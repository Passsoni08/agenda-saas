from apps.tenants.models import TenantMembership


def get_user_role_in_tenant(*, user, tenant) -> str | None:
    membership = TenantMembership.objects.filter(
        user=user,
        tenant=tenant,
        is_active=True,
    ).only("role").first()

    return membership.role if membership else None
