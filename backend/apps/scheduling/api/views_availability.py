from __future__ import annotations

from datetime import datetime, timedelta

from django.db.models import Q
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.scheduling.models import Appointment
from apps.scheduling.api.serializers_availability import AvailabilityQuerySerializer
from common.tenancy.access import get_user_role_in_tenant
from common.tenancy.permissions import HasTenantAccess


class AppointmentAvailabilityView(APIView):
    permission_classes = [IsAuthenticated, HasTenantAccess]

    def get(self, request):
        tenant = request.tenant
        role = get_user_role_in_tenant(user=request.user, tenant=tenant)
        serializer = AvailabilityQuerySerializer(
            data=request.query_params,
            context={"request": request, "role": role},
        )
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data["params"]
        duration_minutes = serializer.validated_data["duration_minutes"]

        tz = timezone.get_current_timezone()

        day_start = timezone.make_aware(
            datetime.combine(params.day, params.work_start), tz
        )
        day_end = timezone.make_aware(
            datetime.combine(params.day, params.work_end), tz
        )

        step = timedelta(minutes=params.step_minutes)
        duration = timedelta(minutes=duration_minutes)

        # appointments do dia para esse professional
        qs = Appointment.objects.filter(
            tenant=request.tenant,
            professional=params.professional,
        ).exclude(status=Appointment.Status.CANCELED)

        # pega os que podem conflitar com o intervalo do dia
        qs = qs.filter(start_at__lt=day_end, end_at__gt=day_start)

        busy = list(qs.values_list("start_at", "end_at"))

        def overlaps(slot_start, slot_end):
            for b_start, b_end in busy:
                if slot_start < b_end and slot_end > b_start:
                    return True
            return False

        slots = []
        cursor = day_start
        while cursor + duration <= day_end:
            slot_start = cursor
            slot_end = cursor + duration
            if not overlaps(slot_start, slot_end):
                slots.append(slot_start.isoformat())
            cursor += step

        return Response(
            {
                "date": params.day.isoformat(),
                "tenant_id": str(request.tenant.id),
                "professional_id": str(params.professional.id),
                "service_id": str(params.service.id),
                "duration_minutes": duration_minutes,
                "step_minutes": params.step_minutes,
                "work_start": params.work_start.strftime("%H:%M"),
                "work_end": params.work_end.strftime("%H:%M"),
                "slots": slots,
                "count": len(slots),
            }
        )
