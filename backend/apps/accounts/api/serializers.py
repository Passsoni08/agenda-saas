from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.tenants.models import TenantMembership, Professional

User = get_user_model()


class MeUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "is_active"]


class MeMembershipSerializer(serializers.ModelSerializer):
    tenant_id = serializers.UUIDField(source="tenant.id", read_only=True)
    tenant_name = serializers.CharField(source="tenant.name", read_only=True)
    tenant_type = serializers.CharField(source="tenant.type", read_only=True)
    tenant_status = serializers.CharField(source="tenant.status", read_only=True)

    class Meta:
        model = TenantMembership
        fields = ["tenant_id", "tenant_name", "tenant_type", "tenant_status", "role", "is_active"]


class MeProfessionalSerializer(serializers.ModelSerializer):
    tenant_id = serializers.UUIDField(source="tenant.id", read_only=True)
    profession_slug = serializers.CharField(source="profession.slug", read_only=True)
    profession_name = serializers.CharField(source="profession.display_name", read_only=True)

    class Meta:
        model = Professional
        fields = [
            "id",
            "tenant_id",
            "display_name",
            "registration_id",
            "is_active",
            "profession_slug",
            "profession_name",
        ]


class MeResponseSerializer(serializers.Serializer):
    user = MeUserSerializer()
    memberships = MeMembershipSerializer(many=True)
    professionals = MeProfessionalSerializer(many=True)
