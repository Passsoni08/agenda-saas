from datetime import datetime, time

from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.tenancy.access import get_user_role_in_tenant
from common.tenancy.permissions import HasTenantAccess
from apps.scheduling.models import Appointment
from apps.tenants.models import Professional

from .serializers import AppointmentListSerializer


class AgendaRangeView(APIView):
    permission_classes = [IsAuthenticated, HasTenantAccess]

    def get(self, request):
        tenant = request.tenant
        role = get_user_role_in_tenant(user=request.user, tenant=tenant)

        start_str = request.query_params.get("start")
        end_str = request.query_params.get("end")

        if not start_str or not end_str:
            return Response(
                {"detail": "Parâmetros 'start' e 'end' são obrigatórios (YYYY-MM-DD)."},
                status=400,
            )

        try:
            start_day = datetime.strptime(start_str, "%Y-%m-%d").date()
            end_day = datetime.strptime(end_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({"detail": "Formato inválido. Use YYYY-MM-DD."}, status=400)

        if end_day < start_day:
            return Response({"detail": "'end' deve ser >= 'start'."}, status=400)

        try:
            professional = self._resolve_professional(request, tenant, role)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)

        include_canceled = request.query_params.get("include_canceled") == "true"

        tz = timezone.get_current_timezone()
        start_dt = timezone.make_aware(datetime.combine(start_day, time.min), tz)
        end_dt = timezone.make_aware(datetime.combine(end_day, time.max), tz)

        qs = (
            Appointment.objects.select_related("client", "professional", "service")
            .filter(
                tenant=tenant,
                professional=professional,
                start_at__gte=start_dt,
                start_at__lte=end_dt,
            )
            .order_by("start_at")
        )

        if not include_canceled:
            qs = qs.exclude(status=Appointment.Status.CANCELED)

        data = AppointmentListSerializer(qs, many=True).data

        return Response(
            {
                "start": start_day.isoformat(),
                "end": end_day.isoformat(),
                "tenant_id": str(tenant.id),
                "professional_id": str(professional.id),
                "include_canceled": include_canceled,
                "value": data,
                "count": len(data),
            }
        )

    def _resolve_professional(self, request, tenant, role):
        if role == "PROVIDER":
            prof = Professional.objects.filter(
                user=request.user,
                tenant=tenant,
                is_active=True,
            ).first()
            if not prof:
                raise ValueError("Professional não encontrado para este usuário no tenant.")
            return prof

        prof_id = request.query_params.get("professional_id")
        if not prof_id:
            raise ValueError("Parâmetro 'professional_id' é obrigatório para OWNER/STAFF.")

        prof = Professional.objects.filter(
            id=prof_id,
            tenant=tenant,
            is_active=True,
        ).first()
        if not prof:
            raise ValueError("professional_id inválido para este tenant.")
        return prof
