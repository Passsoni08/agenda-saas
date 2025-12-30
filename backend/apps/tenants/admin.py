from django.contrib import admin
from .models import Tenant, TenantMembership
from .models import Professional

@admin.register(Professional)
class ProfessionalAdmin(admin.ModelAdmin):
    list_display = ("display_name", "tenant", "profession", "user", "is_active", "created_at")
    list_filter = ("profession", "is_active")
    search_fields = ("display_name", "tenant__name", "user__email", "user__username")


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "status", "created_by", "created_at")
    list_filter = ("type", "status")
    search_fields = ("name",)


@admin.register(TenantMembership)
class TenantMembershipAdmin(admin.ModelAdmin):
    list_display = ("tenant", "user", "role", "is_active", "created_at")
    list_filter = ("role", "is_active")
    search_fields = ("tenant__name", "user__username", "user__email")
