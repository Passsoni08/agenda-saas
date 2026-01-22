from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from common.tenancy.permissions import HasTenantAccess
from apps.clients.models import Client, ClientProfessional
from apps.tenants.models import Professional
from common.tenancy.access import get_user_role_in_tenant
from .serializers import ClientListSerializer, ClientCreateSerializer


class ClientListCreateView(APIView):
    permission_classes = [IsAuthenticated, HasTenantAccess]

    def get(self, request):
        tenant = request.tenant
        q = request.query_params.get("q")

        role = get_user_role_in_tenant(user=request.user, tenant=tenant)

        qs = Client.objects.filter(tenant=tenant, is_active=True)

        # Se for PROVIDER: restringe aos clientes vinculados ao 
        # professional do usuário
        if role == "PROVIDER":
            professional = Professional.objects.get(user=request.user, tenant=tenant, is_active=True)
            qs = qs.filter(
                professional_links__professional=professional,
                professional_links__tenant=tenant,
            )

        if q:
            qs = qs.filter(full_name__icontains=q)

        qs = qs.order_by("full_name").distinct()
        return Response(ClientListSerializer(qs, many=True).data)

    def post(self, request):
        serializer = ClientCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        client = serializer.save()
        return Response(
            ClientListSerializer(client).data, status=status.HTTP_201_CREATED
        )


class ClientDetailView(APIView):
    permission_classes = [IsAuthenticated, HasTenantAccess]

    def get(self, request, client_id):
        tenant = request.tenant
        client = get_object_or_404(Client, id=client_id, tenant=tenant)
        return Response(ClientListSerializer(client).data)
