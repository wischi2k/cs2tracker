# CS2 Tracker (modular + setup)

Dieses Repository ist die konsolidierte Endversion: modulare Architektur mit browserbasiertem Setup.

## Schnellstart

1. Python 3.11+ installieren
2. Abhaengigkeiten installieren:

```bash
python -m venv .venv
# Linux
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

3. Optional `.env` anlegen (siehe `.env.example`)
4. App starten:

```bash
python run.py
```

Fuer Zugriff aus dem lokalen Netzwerk:

- `FLASK_HOST=0.0.0.0` setzen
- im Setup unter "Zugriff auf Web-UI" die Option "Lokales Netzwerk" waehlen

## Zero-Touch Setup

Beim ersten Start wird automatisch auf `/setup` geleitet.

1. `GET /setup` oeffnen
2. Preisupdate-Intervall und Benachrichtigungen setzen
3. Telegram Token + Chat-ID testen und speichern
4. Setup abschliessen

Danach sind Einstellungen unter `/settings` verfuegbar.

## Preisupdates

- Das Intervall in Setup/Settings steuert den internen Auto-Refresh der App.
- Optional kann zusaetzlich ein systemd Timer als Fallback genutzt werden (siehe `docs/OPERATIONS.md`).
- Health-Status zeigt Auto-Refresh unter `GET /health` -> `auto_refresh`.

## Telegram-Zusammenfassung

- Optional aktivierbar in Setup/Settings.
- Konfigurierbar: Intervall in Tagen + Versandzeit (`HH:MM`, Server-Zeitzone).
- Versand laeuft ueber den internen Scheduler.
- Health-Status zeigt Versand unter `GET /health` -> `summary`.

## Sicherheit

- Zugriffsumfang ist konfigurierbar (`nur lokal` oder `lokales Netzwerk`).
- Telegram-Zugangsdaten werden verschluesselt in SQLite (`secret_store`) gespeichert.
- Allgemeine Setup-Werte liegen in `app_config`.

## Dokumentation

- Architektur: `docs/ARCHITECTURE.md`
- Entscheidungen: `docs/DECISIONS.md`
- Betrieb: `docs/OPERATIONS.md`
- Intel NUC + Proxmox: `docs/DEPLOY_INTEL_NUC_PROXMOX.md`

## Projektstruktur

```text
app/
  config.py
  db.py
  domain/
  infrastructure/
  repositories/
  services/
  web/
run.py
templates/
static/
scripts/
```

## Hinweis

`scripts/legacy_app.py` bleibt als Referenz auf den alten monolithischen Stand enthalten.
