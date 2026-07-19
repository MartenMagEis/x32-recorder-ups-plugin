"""The actual safe-shutdown sequence - entirely hardware-independent, entirely in terms of
x32-recorder's existing DB-polled state machine (see x32-recorder's
plugins/PLUGIN_DEVELOPMENT.md: "kein Plugin kann controller_c/controller.c beeinflussen - alles
muss über die bestehenden DB-Felder laufen"). Setting Recording.state = STOP here is exactly
what the normal Stop button does - the already-running C controller notices on its next poll and
stops the recording cleanly, no new controller code needed.
"""
import logging
import subprocess
import time

from django.utils import timezone
from recorder.models import Recording

logger = logging.getLogger(__name__)


def _wait_for_recording_stopped(recording, timeout_s):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        recording.refresh_from_db()
        if recording.state == Recording.STOPPED:
            return True
        time.sleep(1)
    return False


def _jobs_still_running():
    return (
        Recording.objects.filter(mp3_status=Recording.MP3_PROCESSING).exists()
        or Recording.objects.filter(clip_export_status=Recording.CLIPS_PROCESSING).exists()
        or Recording.objects.filter(playback_status=Recording.PLAYBACK_PROCESSING).exists()
    )


def run_safe_shutdown(settings):
    logger.warning("USV: Stromausfall bestätigt - starte sichere Shutdown-Sequenz")

    active = Recording.get_active()
    if active:
        logger.warning(f"USV: stoppe aktive Aufnahme #{active.id} ({active.name!r})")
        active.state = Recording.STOP
        active.save()
        if not _wait_for_recording_stopped(active, timeout_s=30):
            logger.error(
                f"USV: Aufnahme #{active.id} hat nicht innerhalb von 30s STOPPED erreicht - "
                "fahre trotzdem mit dem Warten auf Hintergrund-Jobs fort"
            )
    else:
        logger.info("USV: keine aktive Aufnahme")

    deadline = time.time() + settings.job_wait_timeout_s
    while time.time() < deadline:
        if not _jobs_still_running():
            break
        time.sleep(2)
    else:
        logger.warning(
            f"USV: Zeitlimit ({settings.job_wait_timeout_s}s) für laufende Jobs "
            "(MP3/Export/Wiedergabe-Vorbereitung) erreicht - fahre trotzdem herunter"
        )

    settings.last_power_status = "shutdown_triggered"
    settings.last_checked_at = timezone.now()
    settings.save(update_fields=["last_power_status", "last_checked_at"])

    logger.warning(f"USV: führe Shutdown-Kommando aus: {settings.shutdown_command!r}")
    subprocess.run(settings.shutdown_command, shell=True)
