# x32-recorder USV-Shutdown-Plugin

Ein [x32-recorder](https://github.com/tobire42/x32-recorder)-Plugin (Art `django_app`): erkennt
einen Stromausfall, beendet eine laufende Aufnahme sauber (kein hartes Abschneiden), wartet
(begrenzt) auf laufende Hintergrund-Jobs (MP3-Konvertierung, Song-Export, Wiedergabe-Vorbereitung)
und fährt den Raspberry Pi dann kontrolliert herunter, statt hart die Stromversorgung zu verlieren.

## Wie die Stromausfall-Erkennung funktioniert

Bewusst **hardwareunabhängig konfigurierbar** gehalten (siehe `models.py`,
`UpsPluginSettings.check_kind`), statt fest an ein bestimmtes USV-Board gebunden zu sein:

- **Testmodus** (`always_on`, Default): erkennt nie einen Stromausfall - sicher, um das Plugin
  erstmal ohne Risiko zu installieren und die restliche Sequenz zu testen.
- **GPIO-Pin** (`gpio`): ein BCM-Pin, der bei Stromausfall auf LOW (oder HIGH, konfigurierbar)
  geht - passt zu den meisten einfachen/DIY-USV-Aufbauten (Optokoppler an der Netzteil-Erkennung,
  simple USV-HATs mit Power-Good-Pin).
- **Eigenes Kommando** (`command`): ein beliebiges Shell-Kommando, Exit-Code 0 = Strom vorhanden,
  ungleich 0 = Stromausfall - lässt sich mit jedem Hersteller-CLI-Tool füttern (PiJuice,
  Geekworm, UPS-Lite/MAX17040, ...), ohne dass dieses Plugin die jeweilige Hardware selbst
  kennen muss.

Alle Optionen (inkl. Gnadenfrist gegen kurzes Flackern, Zeitlimit fürs Warten auf Jobs, das
tatsächliche Shutdown-Kommando) sind direkt in x32-recorders **Settings-Seite** editierbar (Plugin-
Karte → "Konfigurieren", nutzt x32-recorders generische Plugin-Web-Konfiguration über
`plugin_config.py`) - alternativ weiterhin über **Django Admin** (`/admin/`, Modell
"USV-Plugin-Einstellungen").

## Sicherheits-Default

Das Plugin ist nach der Installation **deaktiviert** (`enabled = False`) und muss in Django Admin
bewusst aktiviert werden - allein das Hinzufügen/Aktivieren als x32-recorder-Plugin löst noch
nichts aus.

## Installation

Über die x32-recorder Settings-Seite → "Plugins" → GitHub-Link:
`https://github.com/MartenMagEis/x32-recorder-ups-plugin.git` - `plugin.json` wird automatisch
erkannt (Art `django_app`). Nach dem Aktivieren einmal die x32-recorder-Dienste neu starten.

Für den GPIO-Modus zusätzlich manuell installieren:
```
uv pip install -r plugins/x32_recorder_ups_plugin/requirements.txt
```

## Passwortloser Shutdown

Der `shutdown_command` (Default `sudo shutdown -h now`) braucht passwortlosen `sudo` für genau
diesen Befehl - **nicht** blanket-`sudo` für alles:
```
# /etc/sudoers.d/x32-recorder-ups (per `sudo visudo -f ...` anlegen)
pi ALL=(ALL) NOPASSWD: /sbin/shutdown
```
(Benutzername `pi` und Pfad zu `shutdown` ggf. anpassen - `which shutdown`.)

## Testen ohne Risiko

1. In den x32-recorder-Settings (oder Django Admin) `shutdown_command` erstmal auf etwas
   Harmloses setzen, z.B. `echo "USV: shutdown command would fire here" >> /tmp/ups-test.log`.
2. `check_kind` auf `command` stellen, `command` auf ein Skript, das ihr manuell umschalten könnt
   (z.B. `test -f /tmp/power_ok` - Exit 0 solange die Datei existiert).
3. `enabled` aktivieren, `poll_interval_s`/`grace_period_s` niedrig setzen (z.B. 2s/5s) für
   schnelles Testen.
4. Die Test-Datei löschen (Stromausfall simulieren) und in `/tmp/ups-test.log` bzw. den
   x32-recorder-Logs beobachten, dass die Sequenz sauber durchläuft.
5. Erst danach `shutdown_command` auf den echten Befehl und `check_kind` auf die tatsächliche
   Hardware umstellen.

## Warum das ohne Änderungen am C-Controller funktioniert

x32-recorder-Aufnahmen werden ausschließlich über `Recording.state` gesteuert, das der
C-Controller ohnehin laufend pollt - `active.state = Recording.STOP; active.save()` ist exakt das,
was der normale Stop-Button in der UI auch tut. Dieses Plugin braucht deshalb keinen neuen Hook im
Controller, siehe x32-recorders `plugins/PLUGIN_DEVELOPMENT.md`.
