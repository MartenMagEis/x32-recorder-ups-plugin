from django.db import models


class UpsPluginSettings(models.Model):
    """Singleton config, editable for free via Django Admin (see admin.py) - no custom frontend
    needed, matching x32-recorder's plugins/PLUGIN_DEVELOPMENT.md convention."""

    CHECK_ALWAYS_ON = "always_on"
    CHECK_GPIO = "gpio"
    CHECK_COMMAND = "command"
    CHECK_CHOICES = [
        (CHECK_ALWAYS_ON, "Immer eingeschaltet (Testmodus - löst nie aus)"),
        (CHECK_GPIO, "GPIO-Pin (Raspberry Pi, RPi.GPIO)"),
        (CHECK_COMMAND, "Eigenes Kommando"),
    ]

    # Off by default on purpose: installing/enabling the Django app alone must never be enough to
    # risk an unwanted shutdown - this has to be flipped on deliberately, after check_kind is
    # actually configured correctly.
    enabled = models.BooleanField(
        "Aktiviert",
        default=False,
        help_text="Solange aus, überwacht dieses Plugin nichts und kann nichts auslösen."
    )
    check_kind = models.CharField(
        "Erkennungsart", max_length=20, choices=CHECK_CHOICES, default=CHECK_ALWAYS_ON
    )

    # check_kind = gpio
    gpio_pin = models.IntegerField(
        "GPIO-Pin (BCM)", default=17, help_text="BCM-Pin-Nummer, nur für 'GPIO-Pin'."
    )
    gpio_active_low = models.BooleanField(
        "Aktiv bei LOW",
        default=True,
        help_text="An = Pin ist LOW (häufigste Beschaltung mit Pull-up). Aus, wenn dein Board "
                   "das umgekehrt macht."
    )

    # check_kind = command
    command = models.CharField(
        "Eigenes Kommando",
        max_length=512, blank=True, default="",
        help_text="Shell-Kommando, nur für 'Eigenes Kommando'. Exit-Code 0 = Strom vorhanden, "
                   "ungleich 0 = Stromausfall - so lässt sich jedes Hersteller-CLI-Tool "
                   "(PiJuice, Geekworm, ...) einbinden, ohne dass dieses Plugin es selbst kennen muss."
    )

    poll_interval_s = models.IntegerField(
        "Prüfintervall (s)", default=5, help_text="Wie oft der Status geprüft wird."
    )
    grace_period_s = models.IntegerField(
        "Gnadenfrist (s)",
        default=30,
        help_text="Wie lange nach einem erkannten Stromausfall gewartet wird, bevor die "
                   "Shutdown-Sequenz startet - kehrt der Strom in dieser Zeit zurück "
                   "(kurzes Flackern), wird nichts ausgelöst."
    )
    job_wait_timeout_s = models.IntegerField(
        "Job-Wartezeit (s)",
        default=120,
        help_text="Maximale Wartezeit auf eine sauber stoppende Aufnahme und laufende "
                   "Hintergrund-Jobs (MP3-Konvertierung, Song-Export, Wiedergabe-Vorbereitung), "
                   "bevor trotzdem heruntergefahren wird."
    )
    shutdown_command = models.CharField(
        "Shutdown-Kommando",
        max_length=200, default="sudo shutdown -h now",
        help_text="Läuft am Ende der Sequenz. Für Tests hierhin ein harmloses Kommando "
                   "eintragen (z.B. 'echo shutdown-would-fire-here') statt des echten Shutdowns."
    )

    last_power_status = models.CharField("Letzter Status", max_length=100, blank=True, default="")
    last_checked_at = models.DateTimeField("Zuletzt geprüft", null=True, blank=True)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "USV-Plugin-Einstellungen"
