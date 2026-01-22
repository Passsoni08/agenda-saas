from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.tenants.models import Tenant, TenantMembership, Professional

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


class SignupSerializer(serializers.Serializer):
    # credenciais
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    # tenant
    tenant_name = serializers.CharField(max_length=120)
    tenant_type = serializers.ChoiceField(
        choices=Tenant.TenantType.choices,
        default=Tenant.TenantType.SOLO,
    )

    def validate_password(self, value: str) -> str:
        validate_password(value)
        return value

    def validate(self, attrs):
        username = attrs["username"].strip()
        email = attrs["email"].strip().lower()

        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError({"username": "Este username já está em uso."})
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "Este email já está em uso."})

        attrs["username"] = username
        attrs["email"] = email
        return attrs

    def create(self, validated_data):
        username = validated_data["username"]
        email = validated_data["email"]
        password = validated_data["password"]
        tenant_name = validated_data["tenant_name"]
        tenant_type = validated_data["tenant_type"]

        user = User.objects.create_user(username=username, email=email, password=password)

        tenant = Tenant.objects.create(
            name=tenant_name,
            type=tenant_type,
            status=Tenant.Status.PENDING,
            created_by=user,
        )

        TenantMembership.objects.create(
            tenant=tenant,
            user=user,
            role=TenantMembership.Role.OWNER,
            is_active=True,
        )

        return {"user": user, "tenant": tenant}
