from django.db import models

from common.db.models import BaseUUIDModel


class Client(BaseUUIDModel):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="clients")

    full_name = models.CharField(max_length=150)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=30, null=True, blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "client"
        indexes = [
            models.Index(fields=["tenant", "full_name"], name="ix_client_tenant_name"),
        ]

    def __str__(self) -> str:
        return self.full_name


class ClientProfessional(BaseUUIDModel):
    """
    Vínculo N:N entre Cliente e Profissional.
    Permite carteira por profissional e encaminhamento entre profissionais.
    """
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="client_professionals")

    client = models.ForeignKey("clients.Client", on_delete=models.CASCADE, related_name="professional_links")
    professional = models.ForeignKey("tenants.Professional", on_delete=models.CASCADE, related_name="client_links")

    is_primary = models.BooleanField(default=False)

    class Meta:
        db_table = "client_professional"
        constraints = [
            models.UniqueConstraint(fields=["tenant", "client", "professional"], name="uq_client_prof_link"),
        ]

    def __str__(self) -> str:
        return f"{self.client_id} -> {self.professional_id} (primary={self.is_primary})"
