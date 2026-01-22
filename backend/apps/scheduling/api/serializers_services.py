from rest_framework import serializers

from apps.scheduling.models import ServiceDefinition


class ServiceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceDefinition
        fields = [
            "id",
            "name",
            "code",
            "default_duration_minutes",
            "default_price",
            "is_active",
            "created_at",
            "updated_at",
        ]


class ServiceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceDefinition
        fields = [
            "name",
            "code",
            "default_duration_minutes",
            "default_price",
            "is_active",
        ]

    def validate_code(self, value):
        if not value:
            raise serializers.ValidationError("code é obrigatório.")
        return value.strip().lower()
