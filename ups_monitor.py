"""Background poll loop (started once from UpsPluginConfig.ready(), same
threading.Thread(daemon=True) pattern as x32-recorder's own pollers). Debounces a detected power
loss with a grace period before actually triggering the shutdown sequence, so a brief flicker
doesn't take the Pi down mid-rehearsal."""
import logging
import time

from django.utils import timezone

from .power_check import check_power_present
from .shutdown_sequence import run_safe_shutdown

logger = logging.getLogger(__name__)


def _record_status(settings, status):
    settings.last_power_status = status
    settings.last_checked_at = timezone.now()
    settings.save(update_fields=["last_power_status", "last_checked_at"])


def _wait_grace_period(settings):
    """Polls every second during the grace period. Returns True if power was still gone for the
    whole period (proceed to shutdown), False if it came back (abort) - a check failure during
    the grace period counts as "still gone", staying on the cautious side."""
    deadline = time.time() + settings.grace_period_s
    while time.time() < deadline:
        time.sleep(1)
        try:
            if check_power_present(settings):
                return False
        except Exception:
            pass
    return True


def run_ups_monitor():
    from .models import UpsPluginSettings

    while True:
        interval = 5
        try:
            settings = UpsPluginSettings.get_solo()
            interval = settings.poll_interval_s or 5

            if not settings.enabled:
                time.sleep(interval)
                continue

            try:
                power_present = check_power_present(settings)
                _record_status(settings, "ok" if power_present else "lost")
            except Exception as e:
                logger.error(f"USV-Statuscheck fehlgeschlagen: {e}")
                _record_status(settings, f"check_error: {e}"[:100])
                time.sleep(interval)
                continue

            if not power_present:
                logger.warning("USV: Stromausfall erkannt, warte Gnadenfrist ab...")
                if _wait_grace_period(settings):
                    run_safe_shutdown(settings)
                    return  # process is on its way down, no point continuing to poll
                logger.info("USV: Strom kam innerhalb der Gnadenfrist zurück, kein Shutdown ausgelöst")
        except Exception:
            logger.exception("USV-Monitor: unerwarteter Fehler in der Hauptschleife")
        time.sleep(interval)
