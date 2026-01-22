from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from django.utils import timezone
from rest_framework import serializers

from apps.scheduling.models import Appointment, ServiceDefinition
from apps.tenants.models import Professional


@dataclass(frozen=True)
class AvailabilityParams:
    day: date
    service: ServiceDefinition
    professional: Professional
    step_minutes: int
    work_start: time
    work_end: time


class AvailabilityQuerySerializer(serializers.Serializer):
    date = serializers.DateField()
    service_id = serializers.UUIDField()
    professional_id = serializers.UUIDField(required=False)

    def validate(self, attrs):
        request = self.context["request"]
        tenant = request.tenant
        role = self.context["role"]

        # service
        try:
            service = ServiceDefinition.objects.get(
                id=attrs["service_id"], tenant=tenant, is_active=True
            )
        except ServiceDefinition.DoesNotExist:
            raise serializers.ValidationError(
                {"service_id": "Serviço não encontrado neste tenant."}
            )

        duration = getattr(service, "default_duration_minutes", None)
        if not duration or int(duration) <= 0:
            raise serializers.ValidationError(
                {"service_id": "Serviço não possui default_duration_minutes válido."}
            )

        # professional (role-aware)
        if role == "PROVIDER":
            try:
                professional = Professional.objects.get(
                    user=request.user, tenant=tenant, is_active=True
                )
            except Professional.DoesNotExist:
                raise serializers.ValidationError(
                    {
                        "detail": (
                            "Professional não encontrado para este usuário no tenant."
                        )
                    }
                )
        else:
            prof_id = attrs.get("professional_id")
            if prof_id:
                try:
                    professional = Professional.objects.get(
                        id=prof_id, tenant=tenant, is_active=True
                    )
                except Professional.DoesNotExist:
                    raise serializers.ValidationError(
                        {"professional_id": "Professional inválido para este tenant."}
                    )
            else:
                # se o owner também for professional, ok; senão, exigir
                try:
                    professional = Professional.objects.get(
                        user=request.user, tenant=tenant, is_active=True
                    )
                except Professional.DoesNotExist:
                    raise serializers.ValidationError(
                        {
                            "professional_id": (
                                "Informe professional_id (usuário não é um "
                                "Professional no tenant)."
                            )
                        }
                    )

        params = AvailabilityParams(
            day=attrs["date"],
            service=service,
            professional=professional,
            step_minutes=15,
            work_start=time(8, 0),
            work_end=time(18, 0),
        )
        attrs["params"] = params
        attrs["duration_minutes"] = int(duration)
        return attrs
