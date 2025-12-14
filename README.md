CS2 Tracker — Einrichtung & Benutzerhandbuch
===========================================

Kurz: Dieses Projekt sammelt Marktpreise für CS2-Skins, zeigt Charts in einer Web-UI und kann Preisalarme per Telegram senden.

Inhalt
- Voraussetzungen
- Installation
- Datenbank initialisieren & Migrationen
- Umgebungsvariablen (.env)
- App starten
- Kurzanleitung (UI)
- CLI-Skripte
- Features
- Troubleshooting

Voraussetzungen
- Python 3.9+ (Windows: `py` verfügbar)
- Virtuelle Umgebung empfohlen
- Netzwerkzugriff auf `steamcommunity.com`

Installation
1. Virtuelle Umgebung anlegen und aktivieren
```bash
python -m venv venv
# Windows (PowerShell)
venv\Scripts\Activate.ps1
# Windows (cmd)
venv\Scripts\activate.bat
# Linux / macOS
source venv/bin/activate
```
2. Abhängigkeiten installieren
```bash
pip install -r requirements.txt
```

Datenbank initialisieren & Migrationen
1. Neue Datenbank anlegen (nur beim ersten Mal):
```bash
py init_db.py
```
2. Falls das Projekt aktualisiert wurde (neue Spalten), laufen Migrationen im Projektordner. Beispiel: wenn beim Speichern ein Fehler erscheint wegen fehlender Spalte `above_threshold`, führe aus:
```bash
py migrate_add_above_threshold.py
```
Weitere Migrationsskripte im Repo:
- `migrate_add_icon_column.py` — fügt `icon_url` zu `items` hinzu
- `migrate_add_steam_category.py` — fügt `steam_url`/`category` und befüllt Kategorien

Umgebungsvariablen (.env)
Lege eine Datei `.env` im Projektroot an (wird von `telegram_util.py` geladen):
```
TELEGRAM_BOT_TOKEN=123456:ABCdef...
TELEGRAM_CHAT_ID=123456789
```
Wenn diese Variablen fehlen, wird Telegram-Versand deaktiviert und nur auf der Konsole geloggt.

App starten (Entwicklung)
```bash
# mit py auf Windows
py app.py
# oder
python app.py
```
Standard: `http://127.0.0.1:5000` im Browser öffnen.

Wichtige CLI-Skripte
- `fetch_all.py` — holt aktuelle Preise für alle (aktive) Items und speichert Snapshots.
  Beispiel:
  ```bash
  py fetch_all.py
  py fetch_all.py --only-missing
  ```
- `fetch_icons.py` — versucht Icons via Search-API zu holen und in `items.icon_url` zu speichern.
- `weekly_summary.py` — erzeugt eine zusammenfassende Nachricht und sendet sie via Telegram (wenn konfiguriert).
- Migrationen wie `migrate_add_above_threshold.py` (siehe oben)

Benutzung (Web-UI)
- Hinzufügen: Links auf „+ Hinzufügen“ klicken. Entweder Steam Market URL oder direkt Market-Hash eingeben.
- Details: Rechts wird ein Chart mit historischen Preisen angezeigt.
- Sofort-Alarm (Netto ≥): Trage einen Netto-Betrag ein und klicke „Speichern“. Du bekommst:
  - Eine Bestätigung auf der Seite (Flash-Message)
  - Optional eine Telegram-Benachrichtigung (falls `.env` gesetzt)
- Alarm löschen: Eingabefeld leeren und speichern → Alarm wird entfernt.

Features (Übersicht)
- Preis-Snapshots in SQLite (`prices` table)
- Item-Metadaten (Name, Icon, Kategorie)
- Aktiv/Deaktiv-Flag für Items (deaktivierte Items werden nicht mehr abgefragt)
- Sofort-Preisalarme per Schwellenwert (Netto)
- Telegram-Integration für Alarme und Weekly Summary
- Kleine SPA-Logik für Detailansicht (AJAX-Fetch)

Sicherheit & Robustheit
- Alle DB-Statements nutzen Parameterbindung (kein direktes String-Interpolieren in WHEREs).
- Telegram-Fehler werden gefangen und auf Konsole geloggt (nicht fatal).

Troubleshooting (häufige Probleme)
- "sqlite3.OperationalError: table alerts has no column named above_threshold"
  → Migration ausführen:
  ```bash
  py migrate_add_above_threshold.py
  ```

- "Python wurde nicht gefunden" auf Windows
  → Nutze `py` statt `python`, oder aktiviere die virtuelle Umgebung korrekt.

- Telegram sendet nicht
  - Prüfe `.env` auf korrekte `TELEGRAM_BOT_TOKEN` und `TELEGRAM_CHAT_ID`.
  - Bot muss berechtigt sein, Nachrichten an den Chat zu senden (Chat-ID korrekt?).

- App startet nicht / Template-Fehler
  → Prüfe Log-Ausgabe; typischerweise fehlen Endpoints oder Template-`url_for()` Namen. Das Repo wurde aktualisiert — Templates und Endpoints sollten jetzt übereinstimmen.

Weiteres / Erweiterungen
- Hintergrund-Worker (z.B. cron, systemd timer) für `fetch_all.py` empfehlen
- Persistente Logs statt Konsole
- Optionen für Alarm-Trigger (nur einmal, wiederkehrend, Hysterese)

Scheduler / Hintergrund-Tasks
--------------------------------
Kurze Beispiele, wie `fetch_all.py` regelmäßig ausgeführt werden kann.

Windows (Task Scheduler)

1. Öffne die Aufgabenplanung (Task Scheduler) und erstelle eine neue Aufgabe.
2. Trigger: z.B. täglich oder jede 30 Minuten (je nach Bedarf).
3. Aktion: Programm/Script = `py`, Argumente = `fetch_all.py`, Start in = Projektordner (z.B. `E:\Code\cs2tracker_full_package`).

Beispiel (PowerShell):
```powershell
# Einmalig: aktiviere virtuelle Umgebung und starte fetch_all.py
cd 'E:\Code\cs2tracker_full_package'
py fetch_all.py
```

Tipp: Wenn du eine virtuelle Umgebung benutzt, setze `Start in` auf das Verzeichnis und benutze den `py`-Launcher oder einen vollständigen Pfad zur `python.exe` in der venv.

systemd (Linux)

Erstelle eine service- und timer-Datei unter `/etc/systemd/system/`:

`/etc/systemd/system/cs2-fetch.service`
```
[Unit]
Description=CS2 Tracker price fetch

[Service]
Type=oneshot
WorkingDirectory=/path/to/cs2tracker_full_package
ExecStart=/usr/bin/python3 fetch_all.py
```

`/etc/systemd/system/cs2-fetch.timer`
```
[Unit]
Description=Run CS2 price fetch every 30 minutes

[Timer]
OnBootSec=5min
OnUnitActiveSec=30min

[Install]
WantedBy=timers.target
```

Aktivieren & starten:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now cs2-fetch.timer
```

Das startet `fetch_all.py` automatisch nach Boot und alle 30 Minuten.

Dateien
- Haupt-App: `app.py`
- DB-Init: `init_db.py`
- Migrationen: `migrate_add_*`.py
- Telegram-Helper: `telegram_util.py`
- Static / Templates: `static/`, `templates/`

Developer & Project Notes
-------------------------
- Debug- und Hilfsskripte befinden sich im Ordner `scripts/` (z. B. `scripts/inspect_db.py`, `scripts/print_item.py`, `scripts/fetch_icon...`). Diese Skripte sind für lokale Checks gedacht und werden nicht automatisch ausgeführt.
- Icon-Handling: Beim Anlegen eines Items versucht die App automatisch, ein Icon via Steam Search-API zu holen. Wenn kein verifizierter Treffer existiert, kann ein Fallback-Icon gesetzt werden (nur wenn verfügbar). Du kannst ein Icon manuell im Edit-Dialog unter "Icon URL (optional)" setzen.
- Cache-Busting: Um sicherzustellen, dass neu gesetzte Icons sofort im Browser sichtbar sind, hängt die UI einen `cb=<timestamp>` Query-Parameter an Icon-URLs an. Dadurch werden Browser-Caches umgangen, sobald ein Icon geändert oder neu gesetzt wurde.

Git / Deploy Hinweise
---------------------
- Änderungen an Debug-/Testskripten wurden in `scripts/` verschoben, damit das Projekt-Root übersichtlich bleibt.
- Empfohlenes Commit-Verhalten: Test-/Debug-Skripte nicht in die produktive CI einbinden; ggf. in `.gitignore` aufnehmen, falls gewünscht.

Wenn du möchtest, kann ich optional die README noch um einen Abschnitt zur Entwicklung (z. B. wie man neue Migrationsskripte schreibt) oder um Beispielsystemd/Task-Scheduler-Dateien ergänzen.

Wenn du möchtest, kann ich:
- die `README.md` noch auf Englisch übersetzen
- Beispiel-`.env` hinzufügen (`.env.example`)
- eine einfache Systemd Timer / Windows Task-Vorlage für `fetch_all.py` erstellen

---
Dokumentation angelegt: [README.md](README.md)
