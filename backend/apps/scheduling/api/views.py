from __future__ import annotations

from datetime import datetime, timedelta, time

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.scheduling.models import Appointment
from apps.tenants.models import Professional
from common.tenancy.access import get_user_role_in_tenant
from common.tenancy.permissions import HasTenantAccess

from .serializers import (
    AppointmentCreateSerializer,
    AppointmentDetailSerializer,
    AppointmentListSerializer,
)


class AppointmentDayListView(APIView):
    permission_classes = [IsAuthenticated, HasTenantAccess]

    def get(self, request):
        tenant = request.tenant
        role = get_user_role_in_tenant(user=request.user, tenant=tenant)

        date_str = request.query_params.get("date")
        if not date_str:
            return Response(
                {"detail": "Query param 'date' é obrigatório (YYYY-MM-DD)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            day = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"detail": "Formato inválido. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tz = timezone.get_current_timezone()
        start_dt = timezone.make_aware(datetime.combine(day, time.min), tz)
        end_dt = timezone.make_aware(datetime.combine(day, time.max), tz)

        qs = (
            Appointment.objects.select_related(
                "client",
                "professional",
                "service",
            )
            .filter(
                tenant=tenant,
                start_at__gte=start_dt,
                start_at__lte=end_dt,
            )
            .order_by("start_at")
        )

        if role == "PROVIDER":
            professional = Professional.objects.get(
                user=request.user,
                tenant=tenant,
                is_active=True,
            )
            qs = qs.filter(professional=professional)

        data = AppointmentListSerializer(qs, many=True).data
        return Response({"value": data, "count": len(data)})


class AppointmentRangeListView(APIView):
    permission_classes = [IsAuthenticated, HasTenantAccess]

    def get(self, request):
        tenant = request.tenant
        role = get_user_role_in_tenant(user=request.user, tenant=tenant)

        start_str = request.query_params.get("start")
        end_str = request.query_params.get("end")

        if not start_str or not end_str:
            return Response(
                {"detail": "Informe 'start' e 'end' (YYYY-MM-DD)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            start_date = datetime.fromisoformat(start_str).date()
            end_date = datetime.fromisoformat(end_str).date()
        except ValueError:
            return Response(
                {"detail": "Formato inválido. Use YYYY-MM-DD em 'start' e 'end'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if end_date < start_date:
            return Response(
                {"detail": "'end' deve ser maior ou igual a 'start'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tz = timezone.get_current_timezone()
        start_dt = timezone.make_aware(datetime.combine(start_date, time.min), tz)
        end_dt = timezone.make_aware(datetime.combine(end_date, time.max), tz)

        qs = (
            Appointment.objects.select_related(
                "client",
                "professional",
                "service",
            )
            .filter(
                tenant=tenant,
                start_at__lte=end_dt,
                end_at__gte=start_dt,
            )
            .order_by("start_at")
        )

        status_param = request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)

        if role == "PROVIDER":
            professional = Professional.objects.get(
                user=request.user,
                tenant=tenant,
                is_active=True,
            )
            qs = qs.filter(professional=professional)
        else:
            professional_id = request.query_params.get("professional_id")
            if professional_id:
                qs = qs.filter(professional_id=professional_id)

        data = AppointmentListSerializer(qs, many=True).data
        return Response({"value": data, "count": len(data)})


class AppointmentCreateView(APIView):
    permission_classes = [IsAuthenticated, HasTenantAccess]

    def post(self, request):
        tenant = request.tenant
        role = get_user_role_in_tenant(user=request.user, tenant=tenant)

        serializer = AppointmentCreateSerializer(
            data=request.data,
            context={"request": request, "role": role},
        )
        serializer.is_valid(raise_exception=True)
        appt = serializer.save()

        return Response(
            AppointmentListSerializer(appt).data,
            status=status.HTTP_201_CREATED,
        )


class AppointmentCancelView(APIView):
    permission_classes = [IsAuthenticated, HasTenantAccess]

    def patch(self, request, appointment_id):
        tenant = request.tenant
        role = get_user_role_in_tenant(user=request.user, tenant=tenant)

        qs = Appointment.objects.select_related(
            "client",
            "professional",
            "service",
        ).filter(tenant=tenant)

        if role == "PROVIDER":
            professional = Professional.objects.get(
                user=request.user,
                tenant=tenant,
                is_active=True,
            )
            qs = qs.filter(professional=professional)

        appt = get_object_or_404(qs, id=appointment_id)

        if appt.status != Appointment.Status.CANCELED:
            appt.status = Appointment.Status.CANCELED
            appt.save(update_fields=["status", "updated_at"])

        return Response(AppointmentListSerializer(appt).data)


class AppointmentRescheduleView(APIView):
    permission_classes = [IsAuthenticated, HasTenantAccess]

    def patch(self, request, appointment_id):
        tenant = request.tenant
        role = get_user_role_in_tenant(user=request.user, tenant=tenant)

        start_at_raw = request.data.get("start_at")
        if not start_at_raw:
            return Response(
                {"detail": "Campo 'start_at' é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = Appointment.objects.select_related("service", "professional").filter(
            tenant=tenant
        )

        if role == "PROVIDER":
            professional = Professional.objects.get(
                user=request.user,
                tenant=tenant,
                is_active=True,
            )
            qs = qs.filter(professional=professional)

        appt = get_object_or_404(qs, id=appointment_id)

        if appt.status == Appointment.Status.CANCELED:
            return Response(
                {"detail": "Não é possível remarcar um agendamento cancelado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            new_start = datetime.fromisoformat(start_at_raw)
        except ValueError:
            return Response(
                {"detail": "Formato inválido para start_at. Use ISO8601."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if timezone.is_naive(new_start):
            new_start = timezone.make_aware(
                new_start,
                timezone.get_current_timezone(),
            )

        service = appt.service
        duration = (
            getattr(service, "default_duration_minutes", None)
            or getattr(service, "duration_minutes", None)
        )

        if not duration:
            return Response(
                {
                    "detail": (
                        "Serviço não define duração padrão "
                        "(default_duration_minutes)."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_end = new_start + timedelta(minutes=int(duration))

        conflict = (
            Appointment.objects.filter(
                tenant=tenant,
                professional=appt.professional,
            )
            .exclude(id=appt.id)
            .exclude(status=Appointment.Status.CANCELED)
            .filter(start_at__lt=new_end, end_at__gt=new_start)
            .exists()
        )

        if conflict:
            return Response(
                {
                    "detail": (
                        "Conflito de horário: já existe um agendamento para "
                        "este profissional no intervalo informado."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        appt.start_at = new_start
        appt.end_at = new_end
        appt.save(update_fields=["start_at", "end_at", "updated_at"])

        return Response(AppointmentListSerializer(appt).data)


class AppointmentDetailView(APIView):
    permission_classes = [IsAuthenticated, HasTenantAccess]

    def get(self, request, appointment_id):
        tenant = request.tenant
        role = get_user_role_in_tenant(user=request.user, tenant=tenant)

        qs = (
            Appointment.objects.select_related("client", "professional", "service")
            .filter(tenant=tenant)
        )

        if role == "PROVIDER":
            professional = Professional.objects.get(
                user=request.user,
                tenant=tenant,
                is_active=True,
            )
            qs = qs.filter(professional=professional)

        appt = get_object_or_404(qs, id=appointment_id)

        return Response(AppointmentDetailSerializer(appt).data)
