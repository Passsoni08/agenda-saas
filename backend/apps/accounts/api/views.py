from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from apps.tenants.models import TenantMembership, Professional
from .serializers import SignupSerializer, MeResponseSerializer
from common.tenancy.permissions import HasTenantAccess


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        memberships = (
            TenantMembership.objects.select_related("tenant")
            .filter(user=user, is_active=True)
            .order_by("tenant__name")
        )

        professionals = (
            Professional.objects.select_related("tenant", "profession")
            .filter(user=user, is_active=True)
            .order_by("tenant__name", "display_name")
        )

        payload = {
            "user": user,
            "memberships": memberships,
            "professionals": professionals,
        }

        serializer = MeResponseSerializer(payload)
        return Response(serializer.data)


class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        tenant = result["tenant"]
        user = result["user"]

        return Response(
            {
                "user_id": user.id,
                "tenant_id": str(tenant.id),
                "tenant_status": tenant.status,
            },
            status=status.HTTP_201_CREATED,
        )


class TenantPingView(APIView):
    permission_classes = [IsAuthenticated, HasTenantAccess]

    def get(self, request):
        return Response(
            {
                "tenant_id": str(request.tenant.id),
                "tenant_name": request.tenant.name,
                "user_id": request.user.id,
            }
        )
