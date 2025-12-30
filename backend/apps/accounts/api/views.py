from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.tenants.models import TenantMembership, Professional
from .serializers import MeResponseSerializer


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        memberships = (
            TenantMembership.objects
            .select_related("tenant")
            .filter(user=user, is_active=True)
            .order_by("tenant__name")
        )

        professionals = (
            Professional.objects
            .select_related("tenant", "profession")
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
