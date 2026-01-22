from rest_framework import serializers
from apps.clients.models import Client, ClientProfessional
from apps.tenants.models import Professional


class ClientListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ["id", "full_name", "email", "phone", "is_active", "created_at", "updated_at"]


class ClientCreateSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_null=True, allow_blank=True)
    phone = serializers.CharField(max_length=30, required=False, allow_null=True, allow_blank=True)

    professional_id = serializers.UUIDField(required=False)  # opcional, default = professional do usuário

    def create(self, validated_data):
        request = self.context["request"]
        tenant = request.tenant

        professional_id = validated_data.pop("professional_id", None)

        # Determina o professional que ficará vinculado
        if professional_id:
            professional = Professional.objects.get(id=professional_id, tenant=tenant, is_active=True)
        else:
            professional = Professional.objects.get(user=request.user, tenant=tenant, is_active=True)

        client = Client.objects.create(tenant=tenant, **validated_data)

        ClientProfessional.objects.create(
            tenant=tenant,
            client=client,
            professional=professional,
            is_primary=True,
        )

        return client
