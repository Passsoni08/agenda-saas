from django.conf import settings
from django.db import models

from common.db.models import BaseUUIDModel


class Tenant(BaseUUIDModel):
    class TenantType(models.TextChoices):
        SOLO = "SOLO", "Solo"
        CLINIC = "CLINIC", "Clinic"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACTIVE = "ACTIVE", "Active"
        SUSPENDED = "SUSPENDED", "Suspended"

    name = models.CharField(max_length=120)
    type = models.CharField(max_length=10, choices=TenantType.choices, default=TenantType.SOLO)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="tenants_created",
    )

    class Meta:
        db_table = "tenant"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class TenantMembership(BaseUUIDModel):
    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        STAFF = "STAFF", "Staff"
        PROVIDER = "PROVIDER", "Provider"

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tenant_memberships")
    role = models.CharField(max_length=10, choices=Role.choices)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "tenant_membership"
        constraints = [
            models.UniqueConstraint(fields=["tenant", "user"], name="uq_membership_tenant_user"),
        ]

    def __str__(self) -> str:
        return f"{self.user_id} @ {self.tenant_id} ({self.role})"


class Professional(BaseUUIDModel):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="professionals")

    # profissional pode existir “sem login” (ex.: criado pela clínica antes de convidar)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="professional_profiles",
    )

    profession = models.ForeignKey("professions.Profession", on_delete=models.PROTECT, related_name="professionals")
    display_name = models.CharField(max_length=120)
    registration_id = models.CharField(max_length=50, null=True, blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "professional"
        indexes = [
            models.Index(fields=["tenant", "display_name"], name="ix_prof_tenant_name"),
        ]

    def __str__(self) -> str:
        return f"{self.display_name} ({self.profession.slug})"
