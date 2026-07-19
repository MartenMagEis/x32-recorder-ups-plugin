"""Optional web-configuration convention (see x32-recorder's plugins/PLUGIN_DEVELOPMENT.md) -
lets these settings show up inline on x32-recorder's own Settings page instead of only in Django
Admin."""
from recorder.plugin_support import describe_model_fields, model_instance_values

from .models import UpsPluginSettings

FIELDS = [
    "enabled",
    "check_kind",
    "gpio_pin",
    "gpio_active_low",
    "command",
    "poll_interval_s",
    "grace_period_s",
    "job_wait_timeout_s",
    "shutdown_command",
    "last_power_status",
    "last_checked_at",
]
READONLY_FIELDS = {"last_power_status", "last_checked_at"}


def get_config_schema():
    return {"fields": describe_model_fields(UpsPluginSettings, FIELDS, READONLY_FIELDS)}


def get_config_values():
    return model_instance_values(UpsPluginSettings.get_solo(), FIELDS)


def update_config_values(data):
    settings = UpsPluginSettings.get_solo()
    for key, value in data.items():
        if key in FIELDS and key not in READONLY_FIELDS:
            setattr(settings, key, value)
    settings.full_clean(exclude=list(READONLY_FIELDS))
    settings.save()
    return model_instance_values(settings, FIELDS)
