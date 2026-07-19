"""Pluggable "is mains power present?" check - deliberately kept to a few generic mechanisms
instead of hardcoding support for specific UPS boards, so any hardware with a GPIO power-good
pin or its own vendor status tool can be wired in via configuration alone (see
UpsPluginSettings.check_kind in models.py)."""
import subprocess


def check_power_present(settings):
    """Returns True/False. Raises RuntimeError if the check itself couldn't run (missing
    library, bad command, ...) - the caller treats that as "unknown, don't act on it"."""
    if settings.check_kind == settings.CHECK_ALWAYS_ON:
        return True
    if settings.check_kind == settings.CHECK_GPIO:
        return _check_gpio(settings.gpio_pin, settings.gpio_active_low)
    if settings.check_kind == settings.CHECK_COMMAND:
        return _check_command(settings.command)
    raise RuntimeError(f"Unbekannter check_kind: {settings.check_kind!r}")


def _check_gpio(pin, active_low):
    try:
        import RPi.GPIO as GPIO
    except ImportError:
        raise RuntimeError(
            "RPi.GPIO ist nicht installiert (nur auf einem echten Raspberry Pi verfügbar) - "
            "siehe README.md, install_command."
        )
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP if active_low else GPIO.PUD_DOWN)
    value = GPIO.input(pin)
    return (value == GPIO.LOW) if active_low else (value == GPIO.HIGH)


def _check_command(command):
    if not command:
        raise RuntimeError("check_kind ist 'command', aber kein Kommando konfiguriert")
    result = subprocess.run(command, shell=True, capture_output=True, timeout=10)
    return result.returncode == 0
