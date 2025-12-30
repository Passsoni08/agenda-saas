from django.conf import settings
from django.db import models

from common.db.models import BaseUUIDModel


class ServiceDefinition(BaseUUIDModel):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="services")

    code = models.CharField(max_length=40)
    name = models.CharField(max_length=120)

    default_duration_minutes = models.PositiveIntegerField(default=60)
    default_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "service_definition"
        constraints = [
            models.UniqueConstraint(fields=["tenant", "code"], name="uq_service_tenant_code"),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class Appointment(BaseUUIDModel):
    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        COMPLETED = "COMPLETED", "Completed"
        CANCELED = "CANCELED", "Canceled"
        NO_SHOW = "NO_SHOW", "No show"

    class PaidStatus(models.TextChoices):
        UNPAID = "UNPAID", "Unpaid"
        PARTIAL = "PARTIAL", "Partial"
        PAID = "PAID", "Paid"

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="appointments")
    client = models.ForeignKey("clients.Client", on_delete=models.PROTECT, related_name="appointments")
    professional = models.ForeignKey("tenants.Professional", on_delete=models.PROTECT, related_name="appointments")
    service = models.ForeignKey("scheduling.ServiceDefinition", on_delete=models.PROTECT, related_name="appointments")

    start_at = models.DateTimeField()
    end_at = models.DateTimeField()

    status = models.CharField(max_length=12, choices=Status.choices, default=Status.SCHEDULED)

    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_status = models.CharField(max_length=10, choices=PaidStatus.choices, default=PaidStatus.UNPAID)
    payment_method = models.CharField(max_length=30, null=True, blank=True)

    notes = models.TextField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="appointments_created",
    )

    class Meta:
        db_table = "appointment"
        indexes = [
            models.Index(fields=["tenant", "start_at"], name="ix_appt_tenant_start"),
            models.Index(fields=["tenant", "professional", "start_at"], name="ix_appt_prof_start"),
            models.Index(fields=["tenant", "client", "start_at"], name="ix_appt_client_start"),
        ]

    def __str__(self) -> str:
        return f"{self.start_at} - {self.client_id} - {self.professional_id}"
