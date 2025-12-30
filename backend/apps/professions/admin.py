from django.contrib import admin
from .models import Profession


@admin.register(Profession)
class ProfessionAdmin(admin.ModelAdmin):
    list_display = ("display_name", "slug", "created_at")
    search_fields = ("display_name", "slug")
