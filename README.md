# CS2 Tracker

Portfolio-Tracker für CS2 (Counter-Strike 2) Market-Items. Preise werden automatisch über die Steam-Market-API abgerufen, Verläufe gespeichert und optional per Telegram-Zusammenfassung gemeldet.

## Features

- **Item-Verwaltung** — Items per Steam-Market-URL hinzufügen, Kaufpreis hinterlegen, Kategorie setzen
- **Steam-Inventar-Import** — SteamID/Profil-URL eingeben, Inventar-Items per Checkbox auswählen; wiederholbarer Abgleich (abgewählte Items werden deaktiviert, Historie bleibt)
- **Stückzahlen** — mehrere Exemplare als ein Item mit Menge (Kaufpreis = Ø pro Stück); Portfolio-Summen rechnen Preis × Stückzahl
- **Automatische Preisupdates** — interner Scheduler mit konfigurierbarem Intervall (5–1440 Min.)
- **Preishistorie & Chart** — Verlauf pro Item als Zeitreihe (Chart.js)
- **Portfolio-Verlaufschart** — Gesamtwert über Zeit auf dem Dashboard (Snapshot nach jedem Preislauf), Zeiträume 7T/30T/90T/Alles
- **Portfolio-Übersicht** — KPI-Streifen mit Gesamtwert (Brutto/Netto) und Gesamt-Δ auf dem Dashboard
- **Gewinn/Verlust-Anzeige** — Brutto und Netto (Steam-Gebühr 15 %) mit farbigem Glow; Δ Netto als Hauptsignal in Item-Cards und Detail-Panel
- **Detail-Panel mit KPI-Cards** — Kennzahlen (Kaufpreis, Brutto, Netto, Δ Netto) übersichtlich als einzelne Kacheln
- **Preisalarme** — Telegram-Benachrichtigung ab einem konfigurierbaren Netto-Schwellwert
- **Telegram-Zusammenfassung** — periodischer Report mit Top-Gewinnern, Verlierern und wertvollsten Items
- **Theme-System** — 4 wählbare Farbthemes (2 Dark, 2 Light) inkl. Neon-Glow-Effekten und Cursor-Spotlight
- **Browserbasiertes Setup** — kein manuelles Editieren von Dateien nötig

## Themes

Wählbar unter `/settings` → Allgemein:

| Theme | Modus | Stimmung |
|---|---|---|
| Standard Dark | Dark | Neutral, ruhig, täglich nutzbar |
| Highlighter Noir | Dark | Sleek, modern, hochwertig |
| Safety Lime | Light | Hell, bold, Wayfinding-Charakter |
| Cleanroom Lime | Light | Präzise, minimal, datenzentriert |

Alle Themes nutzen CSS Custom Properties (`data-theme` auf `<html>`). Glow-Effekte basieren auf gestapelten `box-shadow`/`text-shadow`-Werten und einem Cursor-folgenden `radial-gradient`-Spotlight pro Karte. Buttons, Inputs und Navigation passen sich automatisch per Design-System-Klassen (`.btn`, `.input`, `.nav-link`) an das aktive Theme an.

## Schnellstart

```bash
python -m venv .venv

# Linux/macOS
source .venv/bin/activate

# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
python run.py
```

Beim ersten Start wird automatisch auf `/setup` weitergeleitet.

Optional `.env` anlegen (siehe `.env.example`):

```env
FLASK_HOST=0.0.0.0      # Netzwerkzugriff
FLASK_PORT=5000
FLASK_DEBUG=false
CS2_DB_PATH=cs2_prices.sqlite
CS2_SECRET_KEY=<eigener_schluessel>
```

## Setup-Assistent

1. `/setup` aufrufen
2. Preisupdate-Intervall, Zugriffs-Scope und Theme wählen
3. Telegram-Bot-Token + Chat-ID testen und speichern
4. Setup abschließen → weiterleitung auf `/`

Einstellungen danach jederzeit unter `/settings` änderbar.

## Preisupdates

Der interne Scheduler läuft als Daemon-Thread. Status und letzter Lauf sind unter `GET /health` → `auto_refresh` einsehbar. Optional kann zusätzlich ein systemd-Timer als Fallback eingerichtet werden (siehe `docs/OPERATIONS.md`).

Steam-Zugriffe werden app-weit koordiniert: Inventar-Import und Preisrefresh teilen sich einen Steam-Lock. Bei HTTP 429 setzt die App einen 15-Minuten-Cooldown und nutzt beim Inventar-Import einen 15-Minuten-Preview-Cache, damit wiederholte Klicks nicht sofort weitere Steam-Requests ausloesen.

## Telegram-Zusammenfassung

Aktivierbar in Setup/Settings. Konfigurierbar: Intervall in Tagen + Versandzeit (`HH:MM`, Serverzeit). Inhalt: Top-3-Gewinner, Top-3-Verlierer, wertvollste Items, Gewinn vs. Kaufpreis. Manueller Versand über „Send now" im Settings-Bereich möglich.

## Sicherheit

- Zugriffs-Scope konfigurierbar: `nur lokal` oder `lokales Netzwerk`
- CSRF-Schutz auf allen Formularen (Flask-WTF); POSTs ohne gültiges Token werden abgelehnt
- Telegram-Zugangsdaten werden verschlüsselt in SQLite (`secret_store`) abgelegt
- Lock-Mechanismus verhindert parallele Scheduler-Läufe (SQLite `BEGIN IMMEDIATE`)
- Zusaetzlicher Steam-Lock verhindert parallele Steam-Requests aus Scheduler und Inventar-Import

## Projektstruktur

```text
app/
  config.py               Flask-Konfiguration (Env-Variablen)
  db.py                   SQLite-Connection-Helper
  domain/
    constants.py          Geteilte Konstanten (STEAM_FEE_RATE)
    models.py             Datenklassen (ItemView, SelectedItemView)
  infrastructure/
    secret_store.py       Verschlüsselung für Secrets
    steam_client.py       Steam-Market-API-Client
    telegram_client.py    Telegram-Bot-Client
  repositories/
    config_repository.py  Konfiguration & Secrets (SQLite)
    item_repository.py    Items, Preise, Alerts (SQLite)
  services/
    import_service.py     Steam-Inventar-Abgleich (Import/Aktivierung)
    item_service.py       Item-Logik, Preisberechnung
    price_scheduler_service.py  Auto-Refresh & Summary-Scheduler
    setup_service.py      Setup-Wizard, Theme-Verwaltung
    summary_service.py    Portfolio-Zusammenfassung, Portfolio-Snapshots
  web/
    routes_health.py      GET /health
    routes_import.py      Steam-Inventar-Import
    routes_items.py       Item-CRUD, Alerts, Refresh
    routes_setup.py       Setup, Settings, Context Processor
run.py                    Einstiegspunkt
templates/                Jinja2-Templates
static/
  css/theme.css           CSS Custom Properties, Themes, Glow-Effekte
  js/glow-effects.js      Cursor-Spotlight per Karte (mousemove)
  js/chart-helpers.js     Chart.js-Hilfsfunktionen
scripts/
  legacy_app.py           Alter monolithischer Stand (Referenz)
docs/
  ARCHITECTURE.md
  DECISIONS.md
  OPERATIONS.md
  DEPLOY_INTEL_NUC_PROXMOX.md
```

## Dokumentation

- **Einsteiger-Installation (Windows/macOS/Linux):** `docs/INSTALLATION.md`
- Architektur & Schichten: `docs/ARCHITECTURE.md`
- Designentscheidungen: `docs/DECISIONS.md`
- Betrieb & systemd: `docs/OPERATIONS.md`
- Deployment Intel NUC + Proxmox: `docs/DEPLOY_INTEL_NUC_PROXMOX.md`
