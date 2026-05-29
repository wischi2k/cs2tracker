# Architektur

## Ziel

Die Anwendung ist in Schichten getrennt, damit Aenderungen lokal bleiben und Tests einfacher werden.

## Schichten

- `app/web`: HTTP-Routen, Request/Response, Rendering
- `app/services`: Business-Logik und Use-Cases
- `app/repositories`: SQL-Zugriffe und Persistenzdetails
- `app/infrastructure`: Externe Schnittstellen (Steam, Telegram, Secret-Crypto)
- `app/domain`: Interne Datenmodelle fuer die App

## Laufzeitfluss (Beispiel `/item/<id>`)

1. Route in `app/web/routes_items.py` empfaengt Request.
2. `ItemService` liefert View-Daten und Chart-Payload.
3. `ItemRepository` liest Daten aus SQLite.
4. Route rendert Template mit den aufbereiteten Daten.

## Laufzeitfluss (Beispiel `/setup`)

1. `routes_setup` prueft Zugriff (lokal/privat) und Setup-Status.
2. `SetupService` liest/schreibt Setup-Werte.
3. `ConfigRepository` persistiert `app_config` und `secret_store`.
4. `TelegramClient` testet Versand optional mit Formularwerten.

## Inversion of Control

Wiring passiert zentral in `app/__init__.py`:

- `ItemRepository`
- `ConfigRepository`
- `SteamClient`
- `TelegramClient`
- `ItemService` (bekommt `telegram` fuer Alert-Versand)
- `SetupService`
- Route-Registrierung

Damit sind Abhaengigkeiten explizit und austauschbar.

## Datenbank

- Datei: per `CS2_DB_PATH`, default `cs2_prices.sqlite`
- Connection: `app/db.py`
- Stabilitaet: `timeout=30` und `PRAGMA busy_timeout=30000`
- Schema-Erstellung:
  - `ItemRepository.ensure_schema()` fuer fachliche Tabellen
  - `ConfigRepository.ensure_schema()` fuer Setup/Secrets

### Tabellen (fachlich)

| Tabelle | Zweck |
|---------|-------|
| `items` | Alle Items (Inventar und Tracking), `item_type IN ('inventory','tracking')` |
| `prices` | Preis-Snapshots je Item und Timestamp |
| `alerts` | Preisalarm pro Item: Schwellenwert, Richtung, Auslöse-Zeitpunkt |

### Item-Typen

- **inventory**: Bereits gekaufte Items. Alert-Schwelle bezieht sich auf den Netto-Verkaufspreis (nach 15 % Steam-Fee).
- **tracking**: Wunschliste. Alert-Schwelle bezieht sich auf den Brutto-Kaufpreis. Standardrichtung: Unterschreitung (≤).

### Alert-Lebenszyklus

1. Alert wird per UI gesetzt (`threshold_net_eur`, `above_threshold`).
2. Nach jedem Preisfetch prüft `ItemService.check_and_fire_alerts()` alle aktiven Alerts.
3. Wird die Bedingung erfüllt: Telegram-Nachricht, `triggered_at` gesetzt, `threshold_net_eur` auf NULL (einmalige Auslösung).
4. `triggered_at` bleibt im Row erhalten und wird als vertikale Linie im Chart dargestellt.

## Endpoint-Kompatibilitaet

Die Route-Registrierung nutzt Endpoint-Namen aus dem Altbestand (`index`, `item`, `add`, `update_item`, `set_alert`, ...), damit bestehende Templates ohne Bruch weiterlaufen.

## Fehlerstrategie

- Externe Calls (Steam/Telegram) sind defensiv und liefern `None`/`False` statt harter Abbrueche.
- Nutzerfluss bleibt stabil: Netzwerkfehler blockieren die UI nicht komplett.

## Naechste Refactor-Schritte

1. `AlertService` separat extrahieren (aktuell in `ItemService`).
2. `PriceService` separat extrahieren.
3. Repository-Tests mit temporaerer SQLite-DB.
4. API-/HTML-Endpunkte schrittweise in Blueprints aufteilen.
