from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.scheduling.models import ServiceDefinition
from common.tenancy.access import get_user_role_in_tenant
from common.tenancy.permissions import HasTenantAccess

from .serializers_services import ServiceCreateSerializer, ServiceListSerializer


class ServiceListCreateView(APIView):
    permission_classes = [IsAuthenticated, HasTenantAccess]

    def get(self, request):
        tenant = request.tenant
        qs = ServiceDefinition.objects.filter(tenant=tenant).order_by("name")
        data = ServiceListSerializer(qs, many=True).data
        return Response({"value": data, "count": len(data)})

    def post(self, request):
        tenant = request.tenant
        role = get_user_role_in_tenant(user=request.user, tenant=tenant)
        if role not in ("OWNER", "STAFF"):
            return Response(
                {"detail": "Sem permissão para criar serviços."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ServiceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = serializer.save(tenant=tenant)

        return Response(
            ServiceListSerializer(service).data,
            status=status.HTTP_201_CREATED,
        )


class ServiceDetailUpdateView(APIView):
    permission_classes = [IsAuthenticated, HasTenantAccess]

    def get(self, request, service_id):
        tenant = request.tenant
        service = get_object_or_404(ServiceDefinition, tenant=tenant, id=service_id)
        return Response(ServiceListSerializer(service).data)

    def patch(self, request, service_id):
        tenant = request.tenant
        role = get_user_role_in_tenant(user=request.user, tenant=tenant)
        if role not in ("OWNER", "STAFF"):
            return Response(
                {"detail": "Sem permissão para editar serviços."},
                status=status.HTTP_403_FORBIDDEN,
            )

        service = get_object_or_404(ServiceDefinition, tenant=tenant, id=service_id)
        serializer = ServiceCreateSerializer(service, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(ServiceListSerializer(service).data)
