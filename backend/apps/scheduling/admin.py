from django.contrib import admin
from .models import ServiceDefinition, Appointment


@admin.register(ServiceDefinition)
class ServiceDefinitionAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "tenant", "default_duration_minutes", "default_price", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "code", "tenant__name")


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("tenant", "professional", "client", "service", "start_at", "end_at", "status", "paid_status", "price")
    list_filter = ("status", "paid_status")
    search_fields = ("client__full_name", "professional__display_name", "tenant__name", "service__name")
