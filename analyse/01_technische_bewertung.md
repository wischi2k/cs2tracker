# Technische Bewertung

Stand: 2026-07-31 · Basis: vollständige Code-Durchsicht von `app/`, `templates/`, `static/`, `scripts/`, `docs/`

## 1. Architektur — Bewertung: sehr gut (für den Zweck)

Die Schichtung ist konsequent umgesetzt und wird auch eingehalten:

```
web/ (Flask-Routes, kein Business-Code)
  → services/ (ItemService, SetupService, SummaryService, PriceSchedulerService)
    → repositories/ (ItemRepository, ConfigRepository — reines SQLite)
    → infrastructure/ (SteamClient, TelegramClient, SecretStore)
domain/ (Datenklassen, Konstanten)
```

Positiv im Detail:

- **Dependency Injection per Hand** in `app/__init__.py` — kein Framework-Magie, alles nachvollziehbar. Für die Projektgröße die richtige Wahl.
- **Routes sind dünn**: `routes_items.py` macht nur Request-Parsing, Delegation, Redirect. Genau richtig.
- **Scheduler-Design** (`price_scheduler_service.py`): Daemon-Thread mit Poll-Loop, Due-Check über persistierten `last_run_ts`, Lock über SQLite `BEGIN IMMEDIATE` mit Lease — überlebt Neustarts sauber und verhindert Doppelläufe. Der Werkzeug-Reloader-Guard (`WERKZEUG_RUN_MAIN`) ist korrekt.
- **Schema-Migration** über `PRAGMA table_info` + `ALTER TABLE` in `ensure_schema()` — pragmatisch und für Single-User-SQLite völlig ausreichend.
- **Fallback-Kaskade im SteamClient** (Search-API exakt → Search-API breit → HTML-Scrape) ist robust gegen die notorisch instabile Steam-API.

Kleinere Architektur-Anmerkungen:

- `ItemService._infer_category` und `SteamClient._normalize_category` duplizieren dieselbe Kategorisierungslogik mit leicht unterschiedlichen Keywords. Gehört einmal in `domain/`.
- `FEE_RATE = 0.15` in `item_service.py:12` dupliziert `domain/constants.py:STEAM_FEE_RATE`. Eine Quelle wählen.
- `routes_items.py:_portfolio_summary` ist Business-Logik in der Web-Schicht — gehört in den `SummaryService` oder `ItemService`.
- `update_item` im Repository: die zwei fast identischen SQL-Zweige (mit/ohne `item_type`) ließen sich mit dynamischem Spalten-Set zusammenfassen.

## 2. Kritische Lücken

### 2.1 Keine Tests (Priorität 1)

Es existiert kein `tests/`-Ordner. Dabei ist der Code durch die DI-Struktur *gut testbar* — die Arbeit wäre dankbar:

- `SteamClient.parse_eur_to_cents` (Komma/Punkt/`--`-Parsing) und `parse_market_hash_from_url` sind pure Funktionen → triviale Unit-Tests.
- `ItemService` mit gemocktem `SteamClient`/`ItemRepository`.
- `SummaryService.build_summary` gegen eine In-Memory-SQLite (`:memory:`).
- Alert-Logik in `check_and_fire_alerts` (above/below × inventory/tracking = 4 Fälle) ist genau die Art Logik, die bei Refactorings still kippt.

Empfehlung: `pytest` + ~20 Tests für Parser, Alert-Logik und Summary. Aufwand: 1–2 Abende.

### 2.2 Kein CSRF-Schutz (Priorität 1 bei LAN-Betrieb)

Alle POST-Endpunkte (`/item/<id>/delete`, `/alert/<id>`, `/settings/*` …) haben keine CSRF-Tokens. Da die App per `ui_access_scope=private_network` bewusst im LAN erreichbar ist, kann jede beliebige Webseite im Browser eines LAN-Nutzers z. B. `POST http://<nuc>:5000/item/1/delete` auslösen. Fix: `Flask-WTF` (`CSRFProtect(app)`) + `{{ csrf_token() }}` in die Formulare. Aufwand: < 1 Stunde.

### 2.3 Fehlende Indizes (Priorität 2, wächst mit der Zeit)

`prices` hat keinen Index. Die korrelierte Subquery „letzter Preis pro Item" in `list_items_with_latest_price` und jede Chart-/Summary-Abfrage scannt die gesamte Preistabelle pro Item. Bei 50 Items × 48 Snapshots/Tag sind das nach einem Jahr ~875.000 Zeilen — auf dem NUC spürbar. Fix in `ensure_schema()`:

```sql
CREATE INDEX IF NOT EXISTS idx_prices_item_ts ON prices(item_id, ts DESC);
```

Zusätzlich sinnvoll: `PRAGMA journal_mode=WAL` in `db.py` — bessere Parallelität zwischen Scheduler-Thread und Web-Requests, weniger `database is locked`-Risiko.

### 2.4 Kein Logging (Priorität 2)

Im gesamten Projekt wird das `logging`-Modul nicht verwendet. `SteamClient` fängt alles mit `except Exception: return None`; der Scheduler speichert nur die letzten 300 Zeichen des letzten Fehlers in der Config-Tabelle. Wenn nachts Preise ausbleiben, gibt es keine Spur, warum. Empfehlung: `logging` mit RotatingFileHandler, `logger.warning` an jeder verschluckten Exception, Log-Zeile pro Scheduler-Lauf (updated/skipped/Dauer).

### 2.5 Verbindungs-Management

Jede Repository-Methode öffnet und schließt eine eigene SQLite-Connection. Besonders teuer in `SummaryService.build_summary`: pro Item bis zu 3 Einzel-Queries mit je eigener Connection (N+1). Für die aktuelle Größe unkritisch, aber bei Wachstum der erste Performance-Hebel: eine Connection pro Request/Operation durchreichen oder die Summary-Queries zu 1–2 Set-basierten Queries zusammenfassen.

## 3. Sicherheit

| Punkt | Bewertung |
|---|---|
| Zugriffs-Scope (lokal/LAN) + Setup nur aus privaten Netzen | ✅ durchdacht, `before_request`-Guard sauber |
| Telegram-Secrets verschlüsselt in SQLite | ⚠️ funktional, aber Eigenbau |
| CSRF | ❌ fehlt komplett (s. o.) |
| SQL-Injection | ✅ durchgängig parametrisierte Queries |
| XSS | ✅ Jinja-Autoescaping aktiv, `html.escape` in Telegram-Nachrichten |
| Secret-Key-Handling | ⚠️ Fallback auf hartkodierten Default-Key |

Zum SecretStore (`secret_store.py`): Der selbstgebaute SHA256-Stream-XOR ist als Konstruktion okay-ish (CTR-artig, zufällige Nonce), hat aber **keine Authentifizierung** (kein MAC — Ciphertext-Manipulation bleibt unbemerkt) und fällt ohne gesetzten `CS2_SECRET_KEY` auf den im Code stehenden Default zurück — dann ist die „Verschlüsselung" nur Verschleierung. Empfehlung: `cryptography.fernet.Fernet` (eine Dependency, authenticated encryption, 10 Zeilen Umbau) und Start-Warnung, wenn der Default-Key aktiv ist.

## 4. Robustheit der Steam-Anbindung

- Der 3s-Delay zwischen Requests (`refresh_all_active_prices`) ist ein guter Anfang, aber bei 429 wird das Item nur übersprungen — **kein Backoff, kein Retry**. Empfehlung: bei 429 den Lauf abbrechen oder exponentiell warten (60s → 120s), sonst produziert ein gedrosselter Lauf viele Lücken in der Historie.
- `fetch_price_cents` nutzt `lowest_price` mit Fallback `median_price` — sinnvoll. Währung ist auf EUR (`currency=3`) hartkodiert; für eine Währungsoption müsste das konfigurierbar werden.
- Die Sequenz `time.sleep(3)` blockiert den Scheduler-Thread pro Lauf um `3 × n` Sekunden — bei 100 Items 5 Minuten. Akzeptabel als Design (Single-Host), sollte aber im `/health`-Status als „running" sichtbar sein, sonst wirkt ein langer Lauf wie ein Hänger.

## 5. Frontend-Technik

- **Tailwind über `cdn.tailwindcss.com`** (`base.html:8`): Das CDN-Script ist explizit nicht für Produktion gedacht (Warnung in der Browser-Konsole, ~300 KB, JIT im Browser) und macht die App **offline-unfähig** — für eine Self-Hosted-LAN-App ein echter Widerspruch. Chart.js + date-fns-Adapter kommen ebenfalls vom CDN. Empfehlung: Tailwind-CLI-Build (eine statische CSS-Datei) oder — da `theme.css` ohnehin ein eigenes Design-System ist — Tailwind ganz entfernen; es wird v. a. für Layout-Utilities genutzt. Chart.js als Datei nach `static/js/` legen.
- `detail_fragment.html` bootet den Chart per `setTimeout`-Polling auf `window.renderDetailChart` — funktioniert, aber ein `defer`-Skript mit `DOMContentLoaded` wäre deterministisch.
- `static/js/router.js` wird von keinem Template eingebunden — toter Code.

## 6. Repo-Hygiene (schnelle Aufräumliste)

Diese Dateien gehören nicht ins Repo bzw. sind tot:

- `cs2_prices.sqlite`, `test_setup_merge.sqlite(-journal)`, `z_test.sqlite(-journal)` — Live-/Test-Datenbanken (in `.gitignore` aufnehmen, aus Git entfernen)
- `__write_test.txt` — Testartefakt
- `static/js/chart-helpers.7z` — Archiv neben der Quelldatei
- `templates/index.txt` — Altstand
- **Tote Templates:** `add_item.html`, `edit_item.html`, `item_detail.html` werden von keiner Route mehr gerendert (nur `add.html`, `edit.html`, `index.html`, `settings.html`, `setup.html` + Includes sind aktiv)
- Doppelte Route `/add-item` neben `/add` (`routes_items.py:213`) — Altlast
- `requirements.txt` ohne Versions-Pinning — mindestens `flask>=3,<4`-artige Grenzen, besser `pip freeze`-Stand als `requirements.lock`

## 7. Priorisierte Maßnahmenliste

| # | Maßnahme | Aufwand | Wirkung | Status |
|---|---|---|---|---|
| 1 | CSRF-Schutz (Flask-WTF) | 1 h | Sicherheit | ✅ umgesetzt (2026-07-31) |
| 2 | Index auf `prices(item_id, ts)` + WAL-Mode | 15 min | Performance dauerhaft | ✅ umgesetzt (2026-07-31) |
| 3 | pytest-Grundstock (Parser, Alerts, Summary) | 1–2 Abende | Wartbarkeit | offen |
| 4 | Logging einführen | 2–3 h | Diagnosefähigkeit | offen |
| 5 | Repo aufräumen (Punkt 6) | 1 h | Hygiene | ✅ umgesetzt (2026-07-31) |
| 6 | Tailwind-CDN ersetzen / entfernen | 2–4 h | Offline-Fähigkeit, Ladezeit | offen |
| 7 | Fernet statt Eigenbau-Krypto | 1 h | Sicherheit | offen |
| 8 | 429-Backoff im Preis-Refresh | 1–2 h | Datenqualität | offen |
