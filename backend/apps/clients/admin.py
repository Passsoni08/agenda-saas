from django.contrib import admin
from .models import Client, ClientProfessional


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("full_name", "tenant", "email", "phone", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("full_name", "email", "phone", "tenant__name")


@admin.register(ClientProfessional)
class ClientProfessionalAdmin(admin.ModelAdmin):
    list_display = ("tenant", "client", "professional", "is_primary", "created_at")
    list_filter = ("is_primary",)
    search_fields = ("client__full_name", "professional__display_name", "tenant__name")
