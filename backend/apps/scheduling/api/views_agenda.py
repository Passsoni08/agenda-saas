from datetime import datetime, time, timedelta

from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.tenancy.access import get_user_role_in_tenant
from common.tenancy.permissions import HasTenantAccess
from apps.scheduling.models import Appointment, ServiceDefinition
from apps.tenants.models import Professional

from .serializers import AppointmentListSerializer


class AgendaDayView(APIView):
    permission_classes = [IsAuthenticated, HasTenantAccess]

    def get(self, request):
        tenant = request.tenant
        role = get_user_role_in_tenant(user=request.user, tenant=tenant)

        date_str = request.query_params.get("date")
        if not date_str:
            return Response(
                {"detail": "Parâmetro 'date' é obrigatório (YYYY-MM-DD)."},
                status=400,
            )

        try:
            day = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"detail": "Formato inválido. Use YYYY-MM-DD."},
                status=400,
            )

        professional = self._resolve_professional(request, tenant, role)

        tz = timezone.get_current_timezone()
        start_dt = timezone.make_aware(datetime.combine(day, time.min), tz)
        end_dt = timezone.make_aware(datetime.combine(day, time.max), tz)

        appts_qs = (
            Appointment.objects.select_related("client", "professional", "service")
            .filter(
                tenant=tenant,
                professional=professional,
                start_at__gte=start_dt,
                start_at__lte=end_dt,
            )
            .order_by("start_at")
        )

        appts_data = AppointmentListSerializer(appts_qs, many=True).data

        service_id = request.query_params.get("service_id")
        slots = []
        if service_id:
            slots = self._build_slots(
                request=request,
                tenant=tenant,
                professional=professional,
                day=day,
                service_id=service_id,
            )

        return Response(
            {
                "date": day.isoformat(),
                "tenant_id": str(tenant.id),
                "professional_id": str(professional.id),
                "appointments": appts_data,
                "appointments_count": len(appts_data),
                "slots": slots,
                "slots_count": len(slots),
            }
        )

    def _resolve_professional(self, request, tenant, role):
        if role == "PROVIDER":
            try:
                return Professional.objects.get(
                    user=request.user,
                    tenant=tenant,
                    is_active=True,
                )
            except Professional.DoesNotExist:
                raise ValueError(
                    "Professional não encontrado para este usuário no tenant."
                )

        prof_id = request.query_params.get("professional_id")
        if not prof_id:
            raise ValueError("Parâmetro 'professional_id' é obrigatório para OWNER/STAFF.")

        try:
            return Professional.objects.get(
                id=prof_id,
                tenant=tenant,
                is_active=True,
            )
        except Professional.DoesNotExist:
            raise ValueError("professional_id inválido para este tenant.")

    def _build_slots(self, request, tenant, professional, day, service_id):
        try:
            service = ServiceDefinition.objects.get(id=service_id, tenant=tenant)
        except ServiceDefinition.DoesNotExist:
            raise ValueError("service_id inválido para este tenant.")

        duration = (
            getattr(service, "default_duration_minutes", None)
            or getattr(service, "duration_minutes", None)
        )
        if not duration:
            raise ValueError("Serviço não define duração (default_duration_minutes).")

        duration = int(duration)

        step_minutes = int(request.query_params.get("step_minutes", 15))
        work_start = request.query_params.get("work_start", "08:00")
        work_end = request.query_params.get("work_end", "18:00")

        ws_h, ws_m = [int(x) for x in work_start.split(":")]
        we_h, we_m = [int(x) for x in work_end.split(":")]

        tz = timezone.get_current_timezone()
        day_start = timezone.make_aware(datetime.combine(day, time(ws_h, ws_m)), tz)
        day_end = timezone.make_aware(datetime.combine(day, time(we_h, we_m)), tz)

        busy_qs = (
            Appointment.objects.filter(
                tenant=tenant,
                professional=professional,
            )
            .exclude(status=Appointment.Status.CANCELED)
            .filter(start_at__lt=day_end, end_at__gt=day_start)
            .only("start_at", "end_at")
        )

        busy = [(a.start_at, a.end_at) for a in busy_qs]

        slots = []
        cur = day_start
        step = timedelta(minutes=step_minutes)
        dur = timedelta(minutes=duration)

        while cur + dur <= day_end:
            candidate_end = cur + dur
            overlaps = any(s < candidate_end and e > cur for s, e in busy)
            if not overlaps:
                slots.append(cur.isoformat())
            cur += step

        return slots
