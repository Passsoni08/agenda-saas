from __future__ import annotations

from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from apps.clients.models import Client
from apps.scheduling.models import Appointment, ServiceDefinition
from apps.tenants.models import Professional


class AppointmentListSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(
        source="client.full_name",
        read_only=True,
    )
    professional_name = serializers.CharField(
        source="professional.display_name",
        read_only=True,
    )
    service_name = serializers.CharField(source="service.name", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "start_at",
            "end_at",
            "status",
            "price",
            "paid_status",
            "client_name",
            "professional_name",
            "service_name",
            "created_at",
            "updated_at",
        ]


class AppointmentDetailSerializer(serializers.ModelSerializer):
    client = serializers.SerializerMethodField()
    professional = serializers.SerializerMethodField()
    service = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            "id",
            "start_at",
            "end_at",
            "status",
            "notes",
            "price",
            "paid_status",
            "payment_method",
            "client",
            "professional",
            "service",
            "created_at",
            "updated_at",
        ]

    def get_client(self, obj):
        return {
            "id": str(obj.client_id),
            "full_name": obj.client.full_name,
            "email": obj.client.email,
            "phone": obj.client.phone,
        }

    def get_professional(self, obj):
        return {
            "id": str(obj.professional_id),
            "display_name": obj.professional.display_name,
        }

    def get_service(self, obj):
        duration = (
            getattr(obj.service, "default_duration_minutes", None)
            or getattr(obj.service, "duration_minutes", None)
        )
        return {
            "id": str(obj.service_id),
            "name": obj.service.name,
            "code": getattr(obj.service, "code", None),
            "default_duration_minutes": duration,
            "default_price": str(getattr(obj.service, "default_price", "")),
        }


class AppointmentCreateSerializer(serializers.Serializer):
    client_id = serializers.UUIDField()
    service_id = serializers.UUIDField()
    start_at = serializers.DateTimeField()

    # Fallback apenas se o service não tiver duração padrão
    duration_minutes = serializers.IntegerField(required=False, min_value=5)

    # Opcionais
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    price = serializers.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
    )
    paid_status = serializers.ChoiceField(
        required=False,
        choices=Appointment.PaidStatus.choices,
    )
    payment_method = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=30,
    )

    # Apenas para OWNER/STAFF (PROVIDER ignora)
    professional_id = serializers.UUIDField(required=False)

    def validate(self, attrs):
        request = self.context["request"]
        tenant = request.tenant
        role = self.context["role"]

        client = self._get_client(
            tenant=tenant,
            client_id=attrs["client_id"],
        )
        service = self._get_service(
            tenant=tenant,
            service_id=attrs["service_id"],
        )
        professional = self._resolve_professional(
            tenant=tenant,
            role=role,
            professional_id=attrs.get("professional_id"),
            user=request.user,
        )

        start_at = attrs["start_at"]
        if timezone.is_naive(start_at):
            start_at = timezone.make_aware(
                start_at,
                timezone.get_current_timezone(),
            )

        duration = self._resolve_duration(service=service, attrs=attrs)
        end_at = start_at + timedelta(minutes=duration)

        self._check_conflict(
            tenant=tenant,
            professional=professional,
            start_at=start_at,
            end_at=end_at,
        )

        attrs["client"] = client
        attrs["service"] = service
        attrs["professional"] = professional
        attrs["start_at"] = start_at
        attrs["end_at"] = end_at
        attrs["duration_resolved"] = duration

        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        tenant = request.tenant

        service = validated_data["service"]

        price = validated_data.get("price")
        if price is None:
            price = getattr(service, "default_price", 0) or 0

        appt = Appointment.objects.create(
            tenant=tenant,
            client=validated_data["client"],
            professional=validated_data["professional"],
            service=service,
            start_at=validated_data["start_at"],
            end_at=validated_data["end_at"],
            status=Appointment.Status.SCHEDULED,
            price=price,
            paid_status=validated_data.get(
                "paid_status",
                Appointment.PaidStatus.UNPAID,
            ),
            payment_method=validated_data.get("payment_method"),
            notes=validated_data.get("notes"),
            created_by=request.user,
        )

        return appt

    # -------------------------
    # Helpers
    # -------------------------

    def _get_client(self, *, tenant, client_id: str) -> Client:
        try:
            return Client.objects.get(id=client_id, tenant=tenant)
        except Client.DoesNotExist as exc:
            raise serializers.ValidationError(
                {"client_id": "Cliente não encontrado neste tenant."}
            ) from exc

    def _get_service(self, *, tenant, service_id: str) -> ServiceDefinition:
        try:
            return ServiceDefinition.objects.get(id=service_id, tenant=tenant)
        except ServiceDefinition.DoesNotExist as exc:
            raise serializers.ValidationError(
                {"service_id": "Serviço não encontrado neste tenant."}
            ) from exc

    def _resolve_professional(
        self,
        *,
        tenant,
        role: str,
        professional_id,
        user,
    ) -> Professional:
        if role == "PROVIDER":
            try:
                return Professional.objects.get(
                    user=user,
                    tenant=tenant,
                    is_active=True,
                )
            except Professional.DoesNotExist as exc:
                raise serializers.ValidationError(
                    {
                        "detail": (
                            "Professional não encontrado para este usuário "
                            "no tenant."
                        )
                    }
                ) from exc

        # OWNER/STAFF
        if professional_id:
            try:
                return Professional.objects.get(
                    id=professional_id,
                    tenant=tenant,
                    is_active=True,
                )
            except Professional.DoesNotExist as exc:
                raise serializers.ValidationError(
                    {
                        "professional_id": (
                            "Professional inválido para este tenant."
                        )
                    }
                ) from exc

        # fallback: tenta usar o próprio usuário como professional
        try:
            return Professional.objects.get(
                user=user,
                tenant=tenant,
                is_active=True,
            )
        except Professional.DoesNotExist as exc:
            raise serializers.ValidationError(
                {
                    "professional_id": (
                        "Informe professional_id (usuário não é um "
                        "Professional no tenant)."
                    )
                }
            ) from exc

    def _resolve_duration(self, *, service: ServiceDefinition, attrs) -> int:
        duration = (
            getattr(service, "default_duration_minutes", None)
            or getattr(service, "duration_minutes", None)
        )

        if not duration:
            duration = attrs.get("duration_minutes")

        if not duration:
            raise serializers.ValidationError(
                {
                    "duration_minutes": (
                        "Obrigatório quando o serviço não define "
                        "default_duration_minutes."
                    )
                }
            )

        duration = int(duration)
        if duration <= 0:
            raise serializers.ValidationError(
                {"duration_minutes": "Duração inválida."}
            )

        return duration

    def _check_conflict(
        self, *, tenant, professional, start_at, end_at
    ) -> None:
        conflict = (
            Appointment.objects.filter(
                tenant=tenant,
                professional=professional,
            )
            .exclude(status=Appointment.Status.CANCELED)
            .filter(start_at__lt=end_at, end_at__gt=start_at)
            .exists()
        )

        if conflict:
            raise serializers.ValidationError(
                {
                    "detail": (
                        "Conflito de horário: já existe um agendamento para "
                        "este profissional no intervalo informado."
                    )
                }
            )
