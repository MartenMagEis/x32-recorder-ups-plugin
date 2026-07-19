import threading

from django.apps import AppConfig

from recorder.plugin_support import should_start_background_work


class UpsPluginConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    # Must match the folder name this repo gets cloned into by x32-recorder's plugin system
    # (derived from the GitHub URL, see recorder.plugins_registry.derive_name_from_github_url) -
    # "x32-recorder-ups-plugin" -> "x32_recorder_ups_plugin".
    name = "x32_recorder_ups_plugin"

    def ready(self):
        if not should_start_background_work():
            return
        from .ups_monitor import run_ups_monitor
        threading.Thread(target=run_ups_monitor, daemon=True).start()
