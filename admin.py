from django.contrib import admin

from .models import UpsPluginSettings


@admin.register(UpsPluginSettings)
class UpsPluginSettingsAdmin(admin.ModelAdmin):
    readonly_fields = ("last_power_status", "last_checked_at")
